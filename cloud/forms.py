from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CloudUser

class CustomUserCreationForm(UserCreationForm):

    class Meta(UserCreationForm):
        model = CloudUser
        fields = ('username', 'email')

class CustomUserChangeForm(UserChangeForm):

    class Meta(UserChangeForm):
        model = CloudUser
        fields = ('username', 'email')