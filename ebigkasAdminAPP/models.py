from django.db import models
from django.contrib.auth.models import User

class Slideshow(models.Model):
    description = models.TextField(null=True)
    added_by = models.ForeignKey(User, related_name='added_by_user',on_delete=models.CASCADE)
    updated_by = models.ForeignKey(User, related_name='updated_by_user',on_delete=models.CASCADE)
    is_active = models.BooleanField(default=False)
    image = models.ImageField(upload_to='slideshow', null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)