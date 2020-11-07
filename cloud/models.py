from django.db import models
from django.contrib.auth.models import AbstractUser


class CloudUser(AbstractUser):
	root_path = models.CharField(max_length=64)
	trash_path = models.CharField(max_length=64)
	pics_default = models.CharField(max_length=64)


class GDrive_Index(models.Model):
	user = models.ForeignKey(CloudUser, on_delete=models.CASCADE)
	gdrive_id = models.CharField(max_length=256, default="", null=True)
	parent_gdrive_id = models.CharField(max_length=256, default="", null=True)
	path = models.CharField(max_length=256) # relative to root_path
	is_dirty = models.BooleanField(default=False)
	is_dir = models.BooleanField(default=False)


class Google_Tokens(models.Model):
	user = models.ForeignKey(CloudUser, on_delete=models.CASCADE)
	g_token = models.CharField(max_length=256, default="", null=True)
	g_refresh_token = models.CharField(max_length=256, default="", null=True)
	gdrive_changes_token = models.CharField(max_length=256, default="", null=True)
