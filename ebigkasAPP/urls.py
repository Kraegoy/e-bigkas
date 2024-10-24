from django.urls import path
from .views import (
    home, 
    profile,
    loginPage, 
    register, 
    logout_view, 
    create_room, 
    room_detail, 
    add_friend, 
    friends_list, 
    search_users_ajax,
    help_view,
    load_videos,
    load_messages,
    get_username,
    friends_conversations,
    reset_unread_count,
    pending_friendships_list,
    accept_friend_request,
    decline_friend_request,
    update_room_status,
    get_recent_calls,
    update_call_duration,
    update_location,
    update_profile_info,
    feedback_view,
    send_feedback,
    remove_friend,
    settings_view,
    verify_email,
    register_email_verification,
    forgot_password, 
    enter_verification_code, 
    reset_password,
    update_voice_preference,
    
)

urlpatterns = [
    path('', home, name='home'),  
    
    path('load_videos/', load_videos, name='load_videos'),
    path('friends_conversations/', friends_conversations, name='friends_conversations'),
    path('login/', loginPage, name='login'),  
    path('register/', register, name='register'),
    path('logout/', logout_view, name='logout'),
    path('help/', help_view, name='help'),
    path('profile/<int:user_id>/', profile, name='profile'),
    path('update_profile_info/', update_profile_info, name='update_profile_info'),
    path('settings/', settings_view, name='settings'),
    path('verify_email/', verify_email, name='verify_email'),  
    path('register/verify-email/<str:email>', register_email_verification, name='register_email_verification'),




    path('create_room/', create_room, name='create_room'),  
    path('room/<str:room_id>/', room_detail, name='room_detail'),
    
    path('add_friend/<int:friend_id>/', add_friend, name='add_friend'),
    path('remove_friend/<int:friend_id>/', remove_friend, name='remove_friend'),

    path('accept_friend_request/<int:friendship_id>/', accept_friend_request, name='accept_friend_request'),
    path('decline_friend_request/<int:friendship_id>/', decline_friend_request, name='decline_friend_request'),
    path('update-location/', update_location, name='update_location'),

    path('friends_list/', friends_list, name='friends_list'),
    path('search/', search_users_ajax, name='search_users_ajax'),
    
    path('load_messages/', load_messages, name='load_messages'),
    path('pending_friendships_list/', pending_friendships_list, name='pending_friendships_list'),
    path('api/get-username/<int:user_id>/', get_username, name='get-username'),
    path('reset_unread_count/<str:conversation_name>/', reset_unread_count, name='reset_unread_count'),
    path('update-room-status/<str:room_id>/<str:status>/', update_room_status, name='update_room_status'),
    path('recent-calls/', get_recent_calls, name='get_recent_calls'),
    path('update_call_duration/<uuid:room_id>/', update_call_duration, name='update_call_duration'),
    
    path('feedback_view/', feedback_view, name='feedback_view'),
    path('send_feedback/', send_feedback, name='send_feedback'),


    path('forgot_password/<str:username>/', forgot_password, name='forgot_password'),
    path('enter_verification_code/', enter_verification_code, name='enter_verification_code'),
    path('reset_password/<str:username>/', reset_password, name='reset_password'),
    path('update-voice-preference/', update_voice_preference, name='update_voice_preference'),

    

]
