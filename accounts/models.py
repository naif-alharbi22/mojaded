from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    image = models.ImageField(upload_to="profile_images/", null=True, blank=True)
    organization = models.ForeignKey("organizations.Organization", on_delete=models.CASCADE, null=True, blank=True)
    pass
