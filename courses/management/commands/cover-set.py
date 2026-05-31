# courses/management/commands/generate_fake_data.py
from django.core.management.base import BaseCommand
import random
import os
from django.conf import settings
from django.core.files.base import ContentFile
from courses.models import Course


class Command(BaseCommand):
    help = 'Set random cover images for all courses'
    
    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        self.cover_images = ['cover1.webp', 'cover2.webp', 'cover3.webp']
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🖼️ start set cover seti...'))
        
        courses = Course.objects.all()
        total_courses = courses.count()
        
        if total_courses == 0:
            self.stdout.write(self.style.WARNING('⚠️ nothing course in data base!'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'📚 {total_courses} find course'))
        
        course_fields = [f.name for f in Course._meta.get_fields()]
        image_field = None
        
        # تشخیص فیلد تصویر
        if 'cover' in course_fields:
            image_field = 'cover'
        elif 'image' in course_fields:
            image_field = 'image'
        elif 'thumbnail' in course_fields:
            image_field = 'thumbnail'
        elif 'course_image' in course_fields:
            image_field = 'course_image'
        else:
            self.stdout.write(self.style.ERROR(f'❌ image field in Course not found'))
            self.stdout.write(self.style.WARNING(f'currnet course: {", ".join(course_fields)}'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'✅ از فیلد "{image_field}" استفاده میشود.'))
        
        successful = 0
        failed = 0
        
        for index, course in enumerate(courses, 1):
            try:
                # انتخاب رندوم یک تصویر از لیست
                selected_image = random.choice(self.cover_images)
                image_path = os.path.join(settings.MEDIA_ROOT, selected_image)
                
                # بررسی وجود فایل
                if not os.path.exists(image_path):
                    self.stdout.write(self.style.WARNING(f'⚠️ file {selected_image} in path {image_path} not exist'))
                    failed += 1
                    continue
                
                # باز کردن و ذخیره فایل
                with open(image_path, 'rb') as f:
                    image_file = ContentFile(f.read(), name=f'course_{course.id}_{selected_image}')
                    
                    # ذخیره در فیلد تشخیص داده شده
                    getattr(course, image_field).save(f'course_{course.id}_{selected_image}', image_file, save=True)
                    course.save()
                    successful += 1
                    
                    # نمایش پیشرفت
                    self.stdout.write(f'✅ {index}/{total_courses} - {course.title} -> {selected_image}')
                
            except Exception as e:
                failed += 1
                self.stdout.write(self.style.ERROR(f'❌ warning for course {course.title}: {str(e)}'))
        
        # گزارش نهایی
        self.stdout.write(self.style.SUCCESS('\n' + '='*50))
        self.stdout.write(self.style.SUCCESS(f'✅ finish op with success'))
        self.stdout.write(self.style.SUCCESS(f'📸 succsess: {successful} course'))
        if failed > 0:
            self.stdout.write(self.style.WARNING(f'⚠️ failed: {failed} course'))
        self.stdout.write(self.style.SUCCESS('='*50))