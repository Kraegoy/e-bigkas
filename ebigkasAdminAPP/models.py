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
    
class Feedback(models.Model):
    FEEDBACK_TYPE_CHOICES = [
        ('bug', 'Bug Report'),
        ('feature', 'Feature Request'),
        ('comment', 'General Comment'),
        ('complaint', 'Complaint'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('reviewed', 'Reviewed'),
        ('resolved', 'Resolved'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feedback')
    feedback_type = models.CharField(max_length=50, choices=FEEDBACK_TYPE_CHOICES)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending')
    response = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.feedback_type}"

    class Meta:
        ordering = ['-created_at']  # Sorts feedback by creation date descending