# base/urls.py
from django.urls import path
from .views import (
    home, 
    profile,
    people,
    loginPage, 
    register, 
    logout_view, 
    create_room, 
    room_detail, 
    add_friend, 
    friends_list, 
    search_users,
    help_view,
    load_videos,
    load_messages,
    get_username,
    friends_conversations,
    reset_unread_count,
)

urlpatterns = [
    path('', home, name='home'),  
    path('load_videos/', load_videos, name='load_videos'),
    path('friends_conversations/', friends_conversations, name='friends_conversations'),
    path('login/', loginPage, name='login'),  
    path('register/', register, name='register'),
    path('logout/', logout_view, name='logout'),
    path('help/', help_view, name='help'),
    path('profile/', profile, name='profile'),
    path('people/', people, name='people'),

    path('create_room/', create_room, name='create_room'),  
    path('room/<str:room_id>/', room_detail, name='room_detail'),
    
    path('add_friend/<int:friend_id>/', add_friend, name='add_friend'),
    path('friends_list/', friends_list, name='friends_list'),
    path('search/', search_users, name='search_users'),
    
    path('load_messages/', load_messages, name='load_messages'),
    path('api/get-username/<int:user_id>/', get_username, name='get-username'),
    path('reset_unread_count/<str:conversation_name>/', reset_unread_count, name='reset_unread_count'),





]
