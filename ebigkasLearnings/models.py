from django.db import models
from django.contrib.auth.models import User  

class Learning(models.Model):
    title = models.CharField(max_length=100)
    action_model = models.IntegerField(default=1)
    model_file_path = models.CharField(max_length=255, null=True)
    belongs_to = models.TextField(default='')  

    def __str__(self):
        return self.title


class UserLearning(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    learning = models.ForeignKey(Learning, on_delete=models.CASCADE)
    learned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'learning')  # Ensure a user can only learn a specific learning once

    def __str__(self):
        return f"{self.user.username} learned {self.learning.title}"
