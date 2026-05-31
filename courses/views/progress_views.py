from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from ..models import Enrollment, VideoProgress, Video
from ..api.serializers import VideoProgressSerializer
from core.permissons import IsStudent

from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers

@method_decorator(cache_page(60 * 15), name='dispatch')
@method_decorator(vary_on_headers('Authorization'), name='dispatch')
class UpdateVideoProgressView(APIView):
    """بروزرسانی پیشرفت تماشای ویدیو"""
    permission_classes = [permissions.IsAuthenticated, IsStudent]
    
    def post(self, request, course_id, video_id):
        enrollment = get_object_or_404(
            Enrollment, 
            student=request.user, 
            course_id=course_id
        )
        video = get_object_or_404(Video, id=video_id)
        
        progress, created = VideoProgress.objects.get_or_create(
            enrollment=enrollment,
            video=video
        )
        
        # بروزرسانی پیشرفت
        is_watched = request.data.get('is_watched', False)
        last_position = request.data.get('last_position', 0)
        
        progress.is_watched = is_watched
        progress.last_position = last_position
        if is_watched and not progress.watched_at:
            from django.utils import timezone
            progress.watched_at = timezone.now()
        progress.save()
        
        # اگر همه ویدیوهای دوره دیده شده، دوره کامل بشه
        total_videos = Video.objects.filter(section__course_id=course_id).count()
        watched_videos = VideoProgress.objects.filter(
            enrollment=enrollment, 
            is_watched=True
        ).count()
        
        if total_videos == watched_videos and not enrollment.is_completed:
            enrollment.is_completed = True
            from django.utils import timezone
            enrollment.completed_at = timezone.now()
            enrollment.save()
        
        return Response({
            'status': 'success',
            'data': VideoProgressSerializer(progress).data
        })