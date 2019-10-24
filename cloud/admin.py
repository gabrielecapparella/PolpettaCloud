from django.contrib import admin

from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import CloudUser

class CustomUserAdmin(UserAdmin):
	add_form = CustomUserCreationForm
	form = CustomUserChangeForm
	model = CloudUser
	list_display = ['username', 'email', 'root_path', 'trash_path']
	fieldsets = (
		(('User'), {'fields': ('username', 'email', 'root_path', 'trash_path')}),
	)

admin.site.register(CloudUser, CustomUserAdmin)