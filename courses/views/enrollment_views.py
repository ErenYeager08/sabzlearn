from rest_framework import status, permissions, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from ..models import Course, Enrollment, Video
from ..api.serializers import EnrollmentSerializer
from core.permissons import IsStudent

from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers

@method_decorator(cache_page(60 * 15), name='dispatch')
@method_decorator(vary_on_headers('Authorization'), name='dispatch')
class EnrollCourseView(APIView):
    """ثبت‌نام در دوره (خرید دوره)"""
    permission_classes = [permissions.IsAuthenticated, IsStudent]
    
    def post(self, request, course_id):
        course = get_object_or_404(Course, id=course_id, is_published=True)
        
        # بررسی ثبت‌نام قبلی
        if Enrollment.objects.filter(student=request.user, course=course).exists():
            return Response({
                'status': 'error',
                'message': 'you have purchased in before'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # ایجاد ثبت‌نام
        enrollment = Enrollment.objects.create(student=request.user, course=course)
        
        return Response({
            'status': 'success',
            'message': 'purchased is successfuly',
            'data': EnrollmentSerializer(enrollment).data
        }, status=status.HTTP_201_CREATED)


@method_decorator(cache_page(60 * 15), name='dispatch')
@method_decorator(vary_on_headers('Authorization'), name='dispatch')
class VideoStreamView(APIView):
    """دریافت اطلاعات ویدیو برای پخش"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, course_slug, video_id):
        # گرفتن دوره و ویدیو
        course = get_object_or_404(Course, slug=course_slug, is_published=True)
        video = get_object_or_404(Video, id=video_id, section__course=course)
        
        # بررسی دسترسی
        user = request.user
        has_access = False
        
        if video.is_free:
            has_access = True
        elif user.is_authenticated:
            has_access = Enrollment.objects.filter(student=user, course=course).exists()
        
        if not has_access:
            return Response({
                'error': 'شما به این ویدیو دسترسی ندارید',
                'need_purchase': not video.is_free
            }, status=status.HTTP_403_FORBIDDEN)
        
        # آدرس کامل ویدیو
        video_url = None
        if video.video_file:
            video_url = request.build_absolute_uri(video.video_file.url)
        
        return Response({
            'id': video.id,
            'title': video.title,
            'video_url': video_url,
            'duration': video.duration,
            'duration_minutes': video.duration_minutes,
            'is_free': video.is_free,
            'course_title': course.title,
            'course_slug': course.slug,
        })

@method_decorator(cache_page(60 * 15), name='dispatch')
@method_decorator(vary_on_headers('Authorization'), name='dispatch')
class CourseContentAccessView(APIView):
    """دسترسی به محتوای دوره (بررسی ثبت‌نام یا رایگان بودن)"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, course_slug, video_id=None):
        course = get_object_or_404(Course, slug=course_slug, is_published=True)
        video = get_object_or_404(Video, id=video_id)
        
        # اگر ویدیو رایگان باشه، دسترسی آزاد
        if video.is_free:
            return Response({
                'status': 'success',
                'video_url': video.video_file.url,
                'is_free': True
            })
        
        # بررسی ثبت‌نام
        if not Enrollment.objects.filter(student=request.user, course=course).exists():
            return Response({
                'status': 'error',
                'message': 'you have\'nt access this course, please purchased this course'
            }, status=status.HTTP_403_FORBIDDEN)
        
        return Response({
            'status': 'success',
            'video_url': video.video_file.url,
            'is_free': False
        })

@method_decorator(cache_page(60 * 15), name='dispatch')
@method_decorator(vary_on_headers('Authorization'), name='dispatch')
class MyCoursesView(generics.ListAPIView):
    """دوره‌هایی که دانشجو خریداری کرده"""
    permission_classes = [permissions.IsAuthenticated, IsStudent]
    serializer_class = EnrollmentSerializer
    
    def get_queryset(self):
        return Enrollment.objects.filter(student=self.request.user)
