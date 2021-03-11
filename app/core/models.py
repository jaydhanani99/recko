from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.conf import settings

class UserManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        """Creates and save a new user"""
        if not email:
            raise ValueError('User must have an email address')
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user
    
    def create_superuser(self, email, password):
        """Creates and save a new super user"""

        user = self.create_user(email, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)

        return user

class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model that supports using email instead of username"""

    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'

class Integration(models.Model):
    name = models.CharField(max_length=255)
    client_id = models.TextField(blank=True, null=True)
    client_secret = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.name

class Account(models.Model):
    BEARER = 'BR'
    TOKEN_TYPE_CHOICES = [
        (BEARER, 'Bearer'),
    ]

    integration = models.ForeignKey(
        Integration,
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    authorization_code = models.TextField(blank=True, null=True)
    scopes = models.TextField(blank=True, null=True)
    access_token = models.TextField(blank=True, null=True)
    expires_in = models.IntegerField(blank=True, null=True)
    refresh_token = models.TextField(blank=True, null=True)
    x_refresh_token_expires_in = models.IntegerField(blank=True, null=True)
    id_token = models.TextField(blank=True, null=True)
    realm_id = models.TextField(blank=True, null=True)
    error_desc = models.TextField(blank=True, null=True)
    error_at = models.DateTimeField(blank=True, null=True)
    token_type = models.CharField(
        max_length=2,
        choices=TOKEN_TYPE_CHOICES,
        default=BEARER,
    )
    is_authenticated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        unique_together = ('integration', 'user',)
    def __str__(self):
        return self.user_id
