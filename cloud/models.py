from django.db import models
from django.contrib.auth.models import AbstractUser


class CloudUser(AbstractUser):
	root_path = models.CharField(max_length=128)
	trash_path = models.CharField(max_length=128)


class GooglePhotosSync(models.Model):
	user = models.ForeignKey(CloudUser, on_delete=models.CASCADE)

	g_token = models.CharField(max_length=256, default="", null=True)
	g_refresh_token = models.CharField(max_length=256, default="", null=True)

	pics_folder = models.CharField(max_length=128)
	last_pic = models.CharField(max_length=256, default="", null=True)
	last_sync = models.DateTimeField(null=True)
	last_sync_result = models.BooleanField(null=True)

