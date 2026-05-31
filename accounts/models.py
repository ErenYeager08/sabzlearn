# accounts/model
from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, AbstractUser
from .managers import UserManager

class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('instructor', 'Instructor'),
        ('admin', 'Admin'),  # ادمین ضعیف API
    )

    phone = models.CharField(max_length=11, unique=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_instructor_approved = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['email']
    objects = UserManager()

    groups = models.ManyToManyField(
        'auth.Group',
        related_name="custom_user_groups",
        blank=True,
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name="custom_user_permissions",
        blank=True,
    )

    # def save(self, *args, **kwargs):
    #     # فقط در زمان ایجاد کاربر جدید و اگر سوپر یوزر نباشد
    #     if not self.pk and not self.is_superuser:
    #         self.role = 'student'
    #         self.is_instructor_approved = False
    #     super().save(*args, **kwargs)

    def save(self, *args, **kwargs):
        # حذف این شرط که role رو اجباری به student تغییر میده
        # فقط برای سوپر یوزر اگر role مشخص نشده بود
        if not self.pk and not self.role and not self.is_superuser:
            self.role = 'student'
            self.is_instructor_approved = False
        super().save(*args, **kwargs)

    @property
    def is_admin_panel(self):
        """آیا می‌تواند وارد پنل ادمین شود؟"""
        return self.is_staff
    
    @property
    def is_full_admin(self):
        """آیا ادمین مطلق است؟"""
        return self.is_superuser
    
    @property
    def can_manage_courses(self):
        """آیا می‌تواند دوره مدیریت کند؟"""
        return self.role in ['instructor', 'admin'] and (self.is_instructor_approved or self.is_superuser)
    
    @property
    def can_manage_users(self):
        """آیا می‌تواند کاربران را مدیریت کند؟"""
        return self.role == 'admin' or self.is_superuser

    def __str__(self):
        return f"{self.phone} - {self.role}"

class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    # user_name = models.CharField(max_length=50, unique=True)
    wallet_balance = models.BigIntegerField(default=0)
    
    def __str__(self):
        return f"Student: {self.user.phone}"

class InstructorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='instructor_profile')
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    profile_image = models.ImageField(upload_to="profiles/", null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    is_verified = models.BooleanField(default=False)
    total_students = models.IntegerField(default=0)
    total_courses = models.IntegerField(default=0)
    
    def __str__(self):
        return f"Instructor: {self.first_name} {self.last_name}"