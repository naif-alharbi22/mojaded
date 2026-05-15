from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()


class ActivityLog(models.Model):

    class Action(models.TextChoices):
        CREATED  = "created",  "أُنشئ"
        UPDATED  = "updated",  "عُدِّل"
        DELETED  = "deleted",  "حُذف"
        EXPIRED  = "expired",  "انتهى"
        RENEWED  = "renewed",  "جُدِّد"
        CANCELLED = "cancelled", "أُلغي"

    class EntityType(models.TextChoices):
        SUBSCRIPTION = "subscription", "اشتراك"
        CLIENT       = "client",       "عميل"
        PLAN         = "plan",         "باقة"
        USER         = "user",         "مستخدم"
        NOTIFICATION = "notification", "تنبيه"

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    org_id      = models.UUIDField(db_index=True)
    user        = models.ForeignKey(
                    User,
                    null=True, blank=True,
                    on_delete=models.SET_NULL,
                    related_name="activity_logs",
                    help_text="None لو العملية تلقائية من النظام"
                  )
    entity_type = models.CharField(max_length=50, choices=EntityType.choices, db_index=True)
    entity_id   = models.UUIDField(db_index=True)
    action      = models.CharField(max_length=20, choices=Action.choices, db_index=True)
    metadata    = models.JSONField(default=dict, blank=True)
    ip_address  = models.GenericIPAddressField(null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "activity_logs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["org_id", "created_at"]),
            models.Index(fields=["entity_type", "entity_id"]),
            models.Index(fields=["org_id", "entity_type", "action"]),
        ]

    def __str__(self):
        actor = self.user.get_full_name() if self.user else "النظام"
        return f"[{self.get_action_display()}] {self.get_entity_type_display()} {self.entity_id} — {actor}"