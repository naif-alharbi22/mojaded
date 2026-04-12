from django.db import models
from django.conf import settings

class Organization(models.Model):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("trial", "Trial"),
        ("suspended", "Suspended"),
    ]

    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_organizations"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="trial",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name