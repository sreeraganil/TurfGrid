from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

class UserManager(BaseUserManager):
    def create_user(self, email, phone, password = None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email)
        user = self.model(phone=phone, email=email, **extra_fields)
        user.set_password(password)
        user.save(using = self._db)
        return user

    def create_superuser(self, email, phone, password = None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, phone, password, **extra_fields)
    
class User(AbstractBaseUser, PermissionsMixin):
    fname = models.CharField(max_length=20)
    lname = models.CharField(max_length=20)
    phone = models.CharField(max_length=10, unique=True)
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    terms_and_conditions = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['phone']

    def __str__(self):
        return self.email
