from django.db import models
from django.contrib.auth.models import AbstractUser


class CloudUser(AbstractUser):
	root_path = models.CharField(max_length=64)
	trash_path = models.CharField(max_length=64)
	pics_default = models.CharField(max_length=64)


class GoogleTokens(models.Model):
	user = models.ForeignKey(CloudUser, on_delete=models.CASCADE)
	g_token = models.CharField(max_length=256, default="", null=True)
	g_refresh_token = models.CharField(max_length=256, default="", null=True)
	last_pic = models.CharField(max_length=256, default="", null=True)

