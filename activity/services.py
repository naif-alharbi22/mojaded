

from .models import ActivityLog


class ActivityLogService:

    @staticmethod
    def log(
        org_id,
        action: str,
        entity_type: str,
        entity_id,
        user=None,
        metadata: dict = None,
        ip_address: str = None,
    ) -> ActivityLog:
        return ActivityLog.objects.create(
            org_id=org_id,
            user=user,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            metadata=metadata or {},
            ip_address=ip_address,
        )

    # ── shortcuts ──────────────────────────────────────────────

    @classmethod
    def subscription_created(cls, org_id, subscription, user, ip=None):
        return cls.log(
            org_id=org_id,
            action=ActivityLog.Action.CREATED,
            entity_type=ActivityLog.EntityType.SUBSCRIPTION,
            entity_id=subscription.id,
            user=user,
            ip_address=ip,
            metadata={
                "client_name": subscription.organization.name,
                "plan_name":   subscription.plan.name,
                "value":       str(subscription.amount),
                "end_date":    str(subscription.next_billing_date),
            },
        )

    @classmethod
    def subscription_renewed(cls, org_id, subscription, user, old_end_date, ip=None):
        return cls.log(
            org_id=org_id,
            action=ActivityLog.Action.RENEWED,
            entity_type=ActivityLog.EntityType.SUBSCRIPTION,
            entity_id=subscription.id,
            user=user,
            ip_address=ip,
            metadata={
                "client_name":  subscription.client.name,
                "old_end_date": str(old_end_date),
                "new_end_date": str(subscription.end_date),
            },
        )

    @classmethod
    def subscription_expired(cls, org_id, subscription):
        """تُستدعى من cron — بدون user"""
        return cls.log(
            org_id=org_id,
            action=ActivityLog.Action.EXPIRED,
            entity_type=ActivityLog.EntityType.SUBSCRIPTION,
            entity_id=subscription.id,
            metadata={
                "client_name": subscription.client.name,
                "plan_name":   subscription.plan.name,
            },
        )

    @classmethod
    def client_created(cls, org_id, client, user, ip=None):
        return cls.log(
            org_id=org_id,
            action=ActivityLog.Action.CREATED,
            entity_type=ActivityLog.EntityType.CLIENT,
            entity_id=client.id,
            user=user,
            ip_address=ip,
            metadata={
                "client_name": client.name,
                "phone":       client.phone,
                "email":       client.email,
            },
        )

    @classmethod
    def subscription_updated(cls, org_id, subscription, user, changed_fields: dict, ip=None):
        """
        changed_fields :
        {"end_date": {"old": "2025-01-01", "new": "2026-01-01"}}
        """
        return cls.log(
            org_id=org_id,
            action=ActivityLog.Action.UPDATED,
            entity_type=ActivityLog.EntityType.SUBSCRIPTION,
            entity_id=subscription.id,
            user=user,
            ip_address=ip,
            metadata={
                "client_name":    subscription.client.name,
                "changed_fields": changed_fields,
            },
        )