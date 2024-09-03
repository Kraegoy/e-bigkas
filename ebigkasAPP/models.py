# Create your models here.
from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserChangeForm
from datetime import timedelta

    
class UserForm(UserChangeForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name']

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to='profile_pics', default='profile_pics/default.png')
    newUser = models.BooleanField(default=True)
    status = models.CharField(max_length=10, default='offline') 

    def __str__(self):
        return f'Profile of {self.user.username}'

class Room(models.Model):
    room_id = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    users = models.ManyToManyField(User, related_name='rooms')
    initiator = models.ForeignKey(User, related_name="room_initiated", on_delete=models.CASCADE)
    status = models.CharField(max_length=10, null=True)

    def __str__(self):
        return self.room_id

class Friendship(models.Model):
    user1 = models.ForeignKey(User, related_name='friendships_as_user1', on_delete=models.CASCADE)
    user2 = models.ForeignKey(User, related_name='friendships_as_user2', on_delete=models.CASCADE)
    initiator = models.ForeignKey(User, related_name='friendships_initiated', on_delete=models.CASCADE)
    status = models.CharField(max_length=10, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user1', 'user2']

    def __str__(self):
        
        if self.user1.id > self.user2.id :
            return f'{self.user1.id} and {self.user2.id}'
        else: 
            return f'{self.user2.id} and {self.user1.id}'


    def save(self, *args, **kwargs):
        created = not self.pk  # Check if this is a new instance
        super().save(*args, **kwargs)
        if created:
            # If this is a new instance, create a conversation for the friendship
            conversation_name = str(self)
            Conversation.objects.create(name=conversation_name, friendship=self)

class Conversation(models.Model):
    name = models.CharField(max_length=255, default='')  # Set default value to an empty string
    friendship = models.OneToOneField(Friendship, on_delete=models.CASCADE, related_name='conversation')
    
class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    timestamp = models.DateTimeField(auto_now_add=True)
    content = models.TextField()
    unread = models.BooleanField(default=True)

class RecentCalls(models.Model):
    room = models.ForeignKey('Room', on_delete=models.CASCADE, related_name='recent_calls')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recent_calls')  # User who has this call in their history
    call_with = models.ForeignKey(User, on_delete=models.CASCADE, related_name='calls_with')  # The other user involved in the call
    is_initiator = models.BooleanField(default=False)
    duration = models.DurationField(default=timedelta(0), null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, null=True, default='missed') 

    
    class Meta:
        ordering = ['-timestamp']  # Orders the calls by the most recent first
        indexes = [
            models.Index(fields=['timestamp']),  # Adding an index for performance optimization
        ]
    
    def __str__(self):
        return f"Call between {self.user} and {self.call_with} at {self.timestamp}"
    
    def end_call(self, end_time):
        """
        Call this method to end the call and set the duration.
        """
        if not self.timestamp:
            raise ValueError("Start time is not set. Cannot calculate duration.")
        self.duration = end_time - self.timestamp
        self.save()