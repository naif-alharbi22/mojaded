from django.db.models.signals import post_save
from django.dispatch import receiver

from organizations.models import Organization
from accounts.models import Role


@receiver(post_save, sender=Organization)
def seed_system_roles(sender, instance, created, **kwargs):
    if created:
        Role.ensure_system_roles(instance)
