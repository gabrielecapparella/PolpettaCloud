from django.db import models
from django.contrib.auth.models import AbstractUser

class CloudUser(AbstractUser):
	root_path = models.CharField(max_length=32)
	trash_path = models.CharField(max_length=32)
	pics_default = models.CharField(max_length=32)

class GoogleSync(models.Model):
	user = models.ForeignKey(CloudUser, on_delete=models.CASCADE)
	path = models.CharField(max_length=128)
	gphotos = models.BooleanField(default=False)
	gdrive = models.BooleanField(default=False)
	is_dir = models.BooleanField(default=False)
	album_id = models.CharField(max_length=128)