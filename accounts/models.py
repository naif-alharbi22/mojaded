from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta

from accounts.permissions import ALL_PERMISSIONS, SYSTEM_ROLES


class Role(models.Model):
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="roles",
    )
    name = models.CharField(max_length=80)
    slug = models.SlugField(max_length=80)
    description = models.CharField(max_length=255, blank=True, default="")
    permissions = models.JSONField(default=list, blank=True)
    is_system = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("organization", "slug")]
        ordering = ["-is_system", "name"]

    def __str__(self):
        return f"{self.name} ({self.organization_id})"

    def clean_permissions(self):
        valid = set(ALL_PERMISSIONS)
        self.permissions = [p for p in (self.permissions or []) if p in valid]

    def save(self, *args, **kwargs):
        self.clean_permissions()
        super().save(*args, **kwargs)

    @classmethod
    def ensure_system_roles(cls, organization):
        for spec in SYSTEM_ROLES:
            cls.objects.update_or_create(
                organization=organization,
                slug=spec["slug"],
                defaults={
                    "name": spec["name"],
                    "description": spec["description"],
                    "permissions": list(spec["permissions"]),
                    "is_system": True,
                },
            )


class User(AbstractUser):
    image = models.ImageField(upload_to="profile_images/", null=True, blank=True)
    organization = models.ForeignKey("organizations.Organization", on_delete=models.CASCADE, null=True, blank=True)
    role = models.ForeignKey(
        Role,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
    )


class PasswordResetCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reset_codes")
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)

    class Meta:
        indexes = [models.Index(fields=["user", "code", "used"])]

    def is_valid(self):
        return not self.used and timezone.now() < self.expires_at

    @classmethod
    def create_for_user(cls, user, ttl_minutes=10):
        import secrets
        cls.objects.filter(user=user, used=False).update(used=True)
        code = f"{secrets.randbelow(1000000):06d}"
        return cls.objects.create(
            user=user,
            code=code,
            expires_at=timezone.now() + timedelta(minutes=ttl_minutes),
        )
