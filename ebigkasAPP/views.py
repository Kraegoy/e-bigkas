# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.shortcuts import redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from .models import Room, Friendship
from django.db.models import Q
from ebigkasAdminAPP.models import Slideshow, Feedback
from ebigkasLearnings.models import Learning, UserLearning
from django.dispatch import receiver
from django.db.models.signals import post_save
from .models import UserProfile, Conversation, Message, RecentCalls
import os
from django.utils import timezone
import logging
import random
logger = logging.getLogger(__name__)


def get_username(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        return JsonResponse({'username': user.username}, status=200)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.userprofile.save()
    
def update_profile_info(request):
    user = User.objects.get(id=request.user.id)
    user_profile = UserProfile.objects.get(user=user)
    if request.method == 'POST':

        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        bio = request.POST.get('bio')
        location = user_profile.location
        
        if first_name:
            user.first_name = first_name
        if last_name:
            user.last_name = last_name
        if bio:
            user_profile.bio = bio
        
        if 'profile_picture' in request.FILES:
            user_profile.profile_picture = request.FILES['profile_picture']       
                    
        user_profile.save()
        user.save()

        return redirect('profile', user_id=request.user.id) 
    
@login_required
def profile(request, user_id):
    user = User.objects.get(id=user_id)
    user_profile = UserProfile.objects.get(user=user)
    friendships = Friendship.objects.filter(Q(user1=user_id) | Q(user2=user_id), status='friends')
    friends_count = friendships.count()

    # Check if a friendship already exists
    isFriends = Friendship.objects.filter(
        Q(user1=request.user, user2=user) | Q(user1=user, user2=request.user)
    ).first()
    
    if isFriends:
        status = isFriends.status 
        IsInitiator = isFriends.initiator == request.user
        
    else:
        status = "Not Friends"
        IsInitiator = None
    
    user_profile_pic = user_profile.profile_picture.url if user_profile.profile_picture else None
    location = user_profile.location 
    bio = user_profile.bio
    context = {       
        'username': user.username,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'date_joined': user.date_joined,
        'user_profile_pic': user_profile_pic,
        'friends_count': friends_count,
        'location' : location,
        'bio' : bio,
        'user_id': user_id,
        'isFriends': isFriends,
        'status': status,
        'IsInitiator': IsInitiator,
    }
    
    return render(request, 'profile.html', context)


@login_required
def add_friend(request, friend_id):
    if request.method == 'POST':
        friend = get_object_or_404(User, id=friend_id)

        # Check if a friendship already exists
        existing_friendship = Friendship.objects.filter(
            Q(user1=request.user, user2=friend) | Q(user1=friend, user2=request.user)
        ).exists()

        if existing_friendship:
            return JsonResponse({'success': False, 'error': 'Friendship already exists'}) 

        # Create a new Friendship object
        Friendship.objects.create(user1=request.user, user2=friend, initiator=request.user)

        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
def remove_friend(request, friend_id):
    if request.method == 'POST':
        friend = get_object_or_404(User, id=friend_id)

        # Check if a friendship already exists
        existing_friendship = Friendship.objects.filter(
            Q(user1=request.user, user2=friend) | Q(user1=friend, user2=request.user)
        )

        if existing_friendship.exists():
            existing_friendship.delete()
            
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
def accept_friend_request(request, friendship_id):
    friendship = get_object_or_404(Friendship, pk=friendship_id)
    if request.user != friendship.initiator:
        friendship.status = 'friends'
        friendship.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
def decline_friend_request(request, friendship_id):
    friendship = get_object_or_404(Friendship, pk=friendship_id)
    if request.user != friendship.initiator:
        friendship.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
def cancel_friend_request(request, friendship_id):
    friendship = get_object_or_404(Friendship, pk=friendship_id)
    if request.user == friendship.initiator:
        friendship.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
def pending_friendships_list(request):
    current_user = request.user
    
    friendships = Friendship.objects.filter(Q(user1=request.user) | Q(user2=request.user))

    # Filter friendships where initiator is not the current user and status is 'pending'
    friendships = Friendship.objects.filter(
        Q(user1=request.user) | Q(user2=request.user),
        ~Q(initiator=current_user),
        status='pending'
    )
        
    pending_user_info = [
        {
            'username': friendship.user1.username if friendship.user2 == current_user else friendship.user2.username,
            'user_id': friendship.user1.id if friendship.user2 == current_user else friendship.user2.id,
            'profile_picture': friendship.user1.userprofile.profile_picture.url if friendship.user2 == current_user else friendship.user2.userprofile.profile_picture.url,
            'friendship_id': friendship.id
        }
        for friendship in friendships
    ]
    return JsonResponse({'success': True, 'pending_user_info': pending_user_info})

@login_required
def friends_list(request):
    # Query all friendships where the current user is either user1 or user2
    friendships = Friendship.objects.filter(Q(user1=request.user) | Q(user2=request.user))

    # Create a list to store the friends
    friends = []

    # Iterate over the friendships and add the corresponding friend info (username, ID, profile picture) to the list
    for friendship in friendships:
        if friendship.status != 'friends':
            continue
        
        if friendship.user1 == request.user:
            friend_user = friendship.user2
        else:
            friend_user = friendship.user1
        
        friend_info = {
            'id': friend_user.id,
            'username': friend_user.username,
            'profile_picture': friend_user.userprofile.profile_picture.url if hasattr(friend_user, 'userprofile') else None,
            'status': friend_user.userprofile.status
        }
        friends.append(friend_info)

    # Return the friends list as JSON
    return JsonResponse({'success': True, 'friends': friends})


def get_friend_suggestions(user):
    # Step 1: Get the user's friends (IDs)
    user_friendships = Friendship.objects.filter(
        Q(user1=user) | Q(user2=user),
        Q(status='friends') | Q(status='pending')
    )
    user_friends_ids = set()
    
    for friendship in user_friendships:
        if friendship.user1 == user:
            user_friends_ids.add(friendship.user2.id)
        else:
            user_friends_ids.add(friendship.user1.id)

    # Step 2: Get the friends of those friends (suggestions), excluding the user's friends and the user themselves
    friend_suggestions = set()
    for friend_id in user_friends_ids:
        friend_friendships = Friendship.objects.filter(Q(user1_id=friend_id) | Q(user2_id=friend_id), status='friends')
        for friendship in friend_friendships:
            if friendship.user1 != user and friendship.user1.id not in user_friends_ids and friendship.user1.id != user.id:
                friend_suggestions.add(friendship.user1)
            if friendship.user2 != user and friendship.user2.id not in user_friends_ids and friendship.user2.id != user.id:
                friend_suggestions.add(friendship.user2)

    # Step 3: Convert the suggestions into a list of user info
    suggestions_list = []
    for suggestion in friend_suggestions:
        suggestions_list.append({
            'id': suggestion.id,
            'username': suggestion.username,
            'profile_picture': suggestion.userprofile.profile_picture.url if hasattr(suggestion, 'userprofile') else None,
            'status': suggestion.userprofile.status
        })
    
    random.shuffle(suggestions_list)

    return suggestions_list





@login_required
def friends_conversations(request):
    # Query all friendships where the current user is either user1 or user2
    friendships = Friendship.objects.filter(Q(user1=request.user) | Q(user2=request.user))

    # Create a list to store the friends and their last message
    friends_with_last_message = []


    for friendship in friendships:
        if friendship.user1 == request.user:
            friend_user = friendship.user2
        else:
            friend_user = friendship.user1
        
        # Get the conversation between the current user and the friend
        conversation = Conversation.objects.filter(
            Q(friendship__user1=request.user, friendship__user2=friend_user) |
            Q(friendship__user1=friend_user, friendship__user2=request.user)
        ).first()
        
        unread_count = 0
        
        last_message = None
        if conversation:
            last_message = conversation.messages.order_by('-timestamp').first()
            unread_count = conversation.messages.filter(unread=True, receiver=request.user).count()

        
        friend_info = {
            'id': friend_user.id,
            'username': friend_user.username,
            'profile_picture': friend_user.userprofile.profile_picture.url if hasattr(friend_user, 'userprofile') else None,
            'status': friend_user.userprofile.status,
            'last_message': {
                'content': last_message.content if last_message else '',
                'timestamp': last_message.timestamp if last_message else '',
                'sender': last_message.sender.id if last_message else '',
            } if last_message else None,
            'unread_count': unread_count
        }
        friends_with_last_message.append(friend_info)

    # Return the friends list with last message as JSON
    return JsonResponse({'success': True, 'friends': friends_with_last_message})


def reset_unread_count(request, conversation_name):
    conversation = get_object_or_404(Conversation, name=conversation_name)
    messages = conversation.messages.filter(unread=True, receiver=request.user)
    messages.update(unread=False)
    return JsonResponse({'success': True})
    
@login_required
def create_room(request):
    if request.method == 'POST':
        # Extract the room ID and user IDs from the POST data
        room_id = request.POST.get('room_id')
        if not room_id:
            return JsonResponse({'error': 'Room ID not provided'}, status=400)

        inviting_user_id = request.POST.get('inviting_user_id')
        invited_user_id = request.POST.get('invited_user_id')

        if not inviting_user_id:
            return JsonResponse({'error': 'Inviting user ID not provided'}, status=400)

        # Fetch the inviting and invited users
        inviting_user = get_object_or_404(User, pk=inviting_user_id)
        invited_user = get_object_or_404(User, pk=invited_user_id)

        # Create or get the room instance
        room, created = Room.objects.get_or_create(room_id=room_id, initiator=inviting_user)

        # Add users to the room
        room.users.add(inviting_user)
        room.users.add(invited_user)
        
         # Create a RecentCalls entry for the inviting user
        RecentCalls.objects.create(
            room=room,
            user=inviting_user,  # Specify the user
            call_with=invited_user,
            is_initiator=True,
            timestamp=room.created_at  # Assuming room has a created_at timestamp
        )

        # Create a RecentCalls entry for the invited user
        RecentCalls.objects.create(
            room=room,
            user=invited_user,  # Specify the user
            call_with=inviting_user,
            is_initiator=False,
            timestamp=room.created_at  # Assuming room has a created_at timestamp
        )

        # Redirect to room detail page
        return redirect('room_detail', room_id=room_id)

    return redirect('home')

def update_call_duration(request, room_id):
    if request.method == 'POST':
        # Fetch the Room object using the room_id
        room = get_object_or_404(Room, room_id=room_id)
        
        # Fetch the RecentCalls instances related to the room
        recent_calls = RecentCalls.objects.filter(room=room)
        
        now = timezone.now()
        
        # Calculate the duration as the difference between the current time and the room's creation time
        duration = now - room.created_at
        
        # Update the duration for all RecentCalls related to this room
        recent_calls.update(duration=duration)
        
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)

def update_room_status(request, room_id, status):
    room = get_object_or_404(Room, room_id=room_id)
    room.status = status
    room.save()
    RecentCalls.objects.filter(room=room).update(status=status)

    return JsonResponse({'success': True})

@login_required
def get_recent_calls(request):
    user = request.user
    
    # Fetch recent calls for the logged-in user
    recent_calls = RecentCalls.objects.filter(user=user).order_by('-timestamp')

    # Prepare the data to be returned
    calls_data = []
    for call in recent_calls[:10]:
        # Get the profile picture URL for the call_with user
        profile_pic_url = None
        try:
            user_profile = UserProfile.objects.get(user=call.call_with)
            if user_profile.profile_picture:
                profile_pic_url = user_profile.profile_picture.url
        except UserProfile.DoesNotExist:
            profile_pic_url = None

        # Convert duration to total seconds
        duration_seconds = call.duration.total_seconds()

        calls_data.append({
            'room_id': call.room.id,
            'call_with': call.call_with.username,
            'call_with_profile_pic': profile_pic_url,
            'duration': duration_seconds,  # Send duration in seconds
            'timestamp': call.timestamp,
            'status': call.status,
            'is_initiator': call.is_initiator
        })
    
    return JsonResponse({'recent_calls': calls_data})


    

@login_required
def room_detail(request, room_id):
    # Retrieve room details based on room_id
    room = get_object_or_404(Room, room_id=room_id)
    # Render the room.html template with the room details
    return render(request, 'room.html', {'room': room})


import json

def load_messages(request):
    if request.method == 'POST':
        # Retrieve the conversationName from the request
        data = json.loads(request.body)
        conversation_name = data.get('conversationName')

        # Filter messages based on the conversationName
        messages = Message.objects.filter(conversation__name=conversation_name).values()

        # Return JSON response with messages data
        return JsonResponse({'messages': list(messages)})
    # Handle other HTTP methods
    return JsonResponse({'error': 'Method not allowed'}, status=405)

def register(request):
    form = UserCreationForm()
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            if User.objects.filter(username__iexact=username).exists():
                messages.error(request, 'Username already exists.')
            else:
                user = form.save(commit=False)
                user.username = username.lower()
                user.save()
                return redirect('login')
        else:
            messages.error(request, 'Try again')
    
    return render(request, 'login.html', {'form': form})


def loginPage(request):
    page = 'login'
    if request.method == 'POST':
        username = request.POST.get('username').lower()
        password = request.POST.get('password')

        if username and password:  # Check if both fields are not empty
            user = authenticate(request, username=username, password=password)
            if user is not None:

                if user.is_staff:
                    login(request, user)
                    return redirect('ebigkas_admin')
                
                login(request, user)
                
                # Update user profile status
                user_profile = UserProfile.objects.get(user=user)
                user_profile.status = 'online'
                user_profile.save()

                # Fetch the newUser status for the logged-in user
                new_user_status = user_profile.newUser

                # Redirect to home page to avoid form resubmission
                return redirect('home')  # Redirect to the homePage view
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Please fill in all fields.')
    
    context = {'page': page}
    return render(request, 'login.html', context)

@login_required
def home(request):
    userProfile = UserProfile.objects.get(user=request.user)  # Get the UserProfile object for the current user
    user_profile_pic = userProfile.profile_picture.url if hasattr(userProfile, 'profile_picture') else None
    isNewUser = userProfile.newUser  # Get the newUser field value from the UserProfile object
    
    # Retrieve active slideshows first, ordered by most recent
    slideshows = Slideshow.objects.filter(is_active=True).order_by('-created_at')
    friend_suggestion = get_friend_suggestions(request.user)  
    
    # Retrieve all learnings
    all_learnings = Learning.objects.all()
    
    # Retrieve UserLearning records for the current user
    learned_learnings = UserLearning.objects.filter(user=request.user).select_related('learning')
    
    # Calculate learned and not learned
    learned_ids = set(learning.learning.id for learning in learned_learnings)
    total_learnings = all_learnings.count()
    learned_count = len(learned_ids)
    not_learned_count = total_learnings - learned_count
    
    # Calculate percentage
    percentage_learned = (learned_count / total_learnings * 100) if total_learnings > 0 else 0

    # Get not learned learnings
    not_learned_learnings = all_learnings.exclude(id__in=learned_ids)

    # Pass the learning data to the template
    return render(request, 'home.html', {
        'isNewUser': isNewUser,
        'user_profile_pic': user_profile_pic,
        'slideshows': slideshows,
        'friend_suggestion': friend_suggestion,
        'learned_count': learned_count,
        'not_learned_count': not_learned_count,
        'percentage_learned': percentage_learned,
        'not_learned_learnings': not_learned_learnings,
    })


@login_required
def search_users_ajax(request):
    query = request.GET.get('query', '')
    users = User.objects.filter(username__icontains=query)
    no_results = users.count() == 0

    current_user = request.user
    user_friendships_as_user1 = Friendship.objects.filter(user1=current_user)
    user_friendships_as_user2 = Friendship.objects.filter(user2=current_user)
    user_friendships = user_friendships_as_user1 | user_friendships_as_user2
    user_friend_ids = [friend.user1_id if friend.user2_id == current_user.id else friend.user2_id for friend in user_friendships]

    users_with_profile_pics = []
    for user in users:
        user_profile = UserProfile.objects.get(user=user)
        profile_picture_url = user_profile.profile_picture.url if user_profile.profile_picture else '/media/profile_pics/default.png'
        
        # Check if the user is a friend
        is_friend = user.id in user_friend_ids

        users_with_profile_pics.append({
            'user_id': user.id,
            'username': user.username,
            'profile_picture': profile_picture_url,
            'is_friend': is_friend
        })

    response_data = {
        'users': users_with_profile_pics,
        'query': query,
        'current_user_id': current_user.id,
        'user_friend_ids': user_friend_ids,
        'no_results': no_results,
    }

    return JsonResponse(response_data)


@login_required
def help_view(request):
    base_dir = os.path.join('static', 'Tutorial Videos')
    folders = []
    for folder_name in os.listdir(base_dir):
        folder_path = os.path.join(base_dir, folder_name)
        if os.path.isdir(folder_path):
            folders.append({'name': folder_name})
    return render(request, 'help.html', {'folders': folders})

@login_required
def load_videos(request):
    if request.method == 'GET':
        folder_name = request.GET.get('folder_name', '')
        base_dir = os.path.join('static', 'Tutorial Videos', folder_name)
        videos = [video for video in os.listdir(base_dir) if video.endswith('.MOV')]
        return JsonResponse({'videos': videos})
    else:
        return JsonResponse({'error': 'Invalid request method'})
    

@login_required
def feedback_view(request):
    # Fetch all feedbacks for the current user
    user_feedbacks = Feedback.objects.filter(user=request.user)

    # Prepare the list of feedbacks
    feedbacks = []
    for feedback in user_feedbacks:
        user_feedback = {
            'feedback_type': dict(Feedback.FEEDBACK_TYPE_CHOICES).get(feedback.feedback_type, 'Unknown'),
            'feedback_message': feedback.message,
            'feedback_date': feedback.created_at,
            'feedback_response': feedback.response
        }
        feedbacks.append(user_feedback)
    
    # Render the feedbacks to the template
    return render(request, 'feedback.html', {'feedbacks': feedbacks})


@login_required
def send_feedback(request):
    if request.method == 'POST':
        feedback_type = request.POST.get('feedback_type')
        message = request.POST.get('message')
        user = request.user  
        
        # Create and save the feedback instance
        feedback = Feedback.objects.create(
            user=user,
            feedback_type=feedback_type,
            message=message
        )
        messages.success(request, 'Thank you for your feedback!')

    return redirect('feedback_view')

@login_required
def update_location(request):
    if request.method == 'POST':
        country = request.POST.get('country')
        city = request.POST.get('city')
        barangay = request.POST.get('barangay')
        
        location = f'{country}, {city}, {barangay}'
        user_profile = request.user.userprofile
        user_profile.location = location
        user_profile.save()
        
        return redirect('profile', request.user.id)  

    return render(request, 'profile.html')

@login_required
def logout_view(request):
    
    user_profile = UserProfile.objects.get(user=request.user)
    user_profile.status = 'offline'
    user_profile.save()
    
    logout(request)
    return redirect('login')






