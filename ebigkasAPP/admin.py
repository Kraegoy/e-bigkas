from django.contrib import admin
from .models import Room, Friendship, UserProfile, Message, Conversation,RecentCalls

admin.site.register(Room)
admin.site.register(Friendship)
admin.site.register(UserProfile)
admin.site.register(Message)
admin.site.register(Conversation)
admin.site.register(RecentCalls)



