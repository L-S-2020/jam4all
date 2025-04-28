from django.db import models

# Create your models here.

class User(models.Model):
    spotify_id = models.CharField(unique=True, max_length=255)
    spotify_username = models.CharField(max_length=255)
    spotify_access_token = models.CharField(max_length=255)
    spotify_refresh_token = models.CharField(max_length=255)
    spotify_token_expires = models.DateTimeField()

class Jam(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    jam_name = models.CharField(max_length=255)
    jam_description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    access_code = models.CharField(max_length=8, unique=True)
    is_active = models.BooleanField(default=True)
