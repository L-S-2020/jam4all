from datetime import timedelta
from django.utils import timezone

from django.db import models

# Create your models here.

class User(models.Model):
    spotify_id = models.CharField(unique=True, max_length=255)
    spotify_username = models.CharField(max_length=255)
    spotify_access_token = models.CharField(max_length=255)
    spotify_refresh_token = models.CharField(max_length=255)
    spotify_token_expires = models.IntegerField()

class Jam(models.Model):
    code = models.CharField(max_length=8, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE,)
    jam_name = models.CharField(max_length=255)
    jam_description = models.TextField(default="")
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    queue = models.TextField()
    last_queue_update = models.DateTimeField(auto_now=True)
    market = models.CharField(max_length=4, default="DE")

    def name(self):
        if self.jam_name == "":
            return f"Jam at {self.created_at.strftime('%Y-%m-%d %H:%M')}"
        return self.jam_name
