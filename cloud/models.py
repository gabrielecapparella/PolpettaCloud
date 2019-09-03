from django.db import models
from django.contrib.auth.models import AbstractUser

class CloudUser(AbstractUser):
	root_path = models.CharField(max_length=32)
	trash_path = models.CharField(max_length=32)
