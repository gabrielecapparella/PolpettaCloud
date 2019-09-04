from django.db import models
from django.contrib.auth.models import AbstractUser

class CloudUser(AbstractUser):
	root_path = models.CharField(max_length=32)
	trash_path = models.CharField(max_length=32)

class GoogleSync(models.Model):
	user = models.ForeignKey(CloudUser, on_delete=models.CASCADE)
	path = models.CharField(max_length=32)
	gphotos = models.BooleanField(default=False)
	gdrive = models.BooleanField(default=False)