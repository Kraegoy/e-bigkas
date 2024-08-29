from django import forms
from django.contrib.auth.models import User
from .models import UserProfile

class AddFriendForm(forms.Form):
    friend_username = forms.CharField(label='Friend Username')

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['profile_picture']

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name']