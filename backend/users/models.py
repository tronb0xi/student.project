from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, phone_number, password=None, **extra_fields):
        if not phone_number:
            raise ValueError('The Phone Number field must be set')
        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'ADMIN')
        return self.create_user(phone_number, password, **extra_fields)


class User(AbstractUser):
    username = None
    phone_number = models.CharField(max_length=15, unique=True)
    ROLE_CHOICES = [('ADMIN', 'Administrator'), ('TEACHER', 'Teacher')]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='ADMIN')
    is_active = models.BooleanField(default=True)
    objects = UserManager()
    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = []

    def __str__(self):
        return f"{self.phone_number} ({self.get_role_display()})"
