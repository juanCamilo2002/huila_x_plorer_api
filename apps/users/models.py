from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)

    ROLE_CHOICES = (
        ('USER', 'Mobile User'),
        ('ADMIN', 'Admin')
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='USER'
    )

    phone = models.CharField(max_length=20, blank=True, null=True)

    avatar = models.ImageField(
        upload_to='users/avatars/',
        blank=True,
        null=True
    )

    is_verified = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        db_table = 'users'

    def __str__(self):
        return self.email
    

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'.strip()
