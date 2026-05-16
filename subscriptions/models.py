from django.db import models
from django.forms import ValidationError
from organizations.models import Organization
from customers.models import Customer
from dateutil.relativedelta import relativedelta
from billing.models import Invoice
from django.utils import timezone
from common.managers import TenantManager
from django.utils.translation import gettext as _


class Plan(models.Model):
    objects = TenantManager()
    BILLING_CYCLE_CHOICES = [
        ("monthly", "Monthly"),
        ("yearly", "Yearly"),
    ]

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="plans"
    )

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    billing_cycle = models.CharField(
        max_length=10,
        choices=BILLING_CYCLE_CHOICES,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class SubscriptionStatus(models.Model):
    name = models.CharField(max_length=20, unique=True)
    Organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="subscription_statuses",
    )
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class Subscription(models.Model):
    objects = TenantManager()

    
    TYPE_CHOICES = [
        ("yearly", _("Yearly")),
        ("monthly", _("Monthly")),
    ]
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="subscriptions"
    )

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="subscriptions"
    )
    subscription_type = models.CharField(max_length=50, default="monthly", choices=TYPE_CHOICES)
    plan = models.ForeignKey(
        Plan,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    amount = models.DecimalField(max_digits=10, decimal_places=2 , default=0)

    updated_at = models.DateTimeField(auto_now=True)

    start_date = models.DateField()
    next_billing_date = models.DateField(null=True, blank=True)

    status = models.ForeignKey(
        SubscriptionStatus,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    duration_months = models.PositiveIntegerField(default=1)


    created_at = models.DateTimeField(auto_now_add=True)

    note = models.TextField(blank=True, null=True)

    
    def save(self, *args, **kwargs):

        if self.start_date:

            duration = self.duration_months or 1

            if self.subscription_type == "monthly":
                self.next_billing_date = self.start_date + relativedelta(
                    months=duration
                )

            elif self.subscription_type == "yearly":
                self.next_billing_date = self.start_date + relativedelta(
                    years=duration
                )

        super().save(*args, **kwargs)
    
    def clean(self):
        if self.duration_months <= 0:
            raise ValidationError("Duration must be greater than zero.")


    
    
    class Meta:
        indexes = [
            models.Index(fields=["organization", "status"]),
            models.Index(fields=["next_billing_date"]),
        ]



    @property
    def total_amount(self):
        total = self.amount or 0

        for sub_addon in self.subscription_addons.all():
            if sub_addon.addon.billing_type == "one_time":
                if not sub_addon.is_consumed:
                    total += sub_addon.amount
            else:
                total += sub_addon.amount

        return total



class AddOn(models.Model):
    objects = TenantManager()

    BILLING_TYPE_CHOICES = [
        ("monthly", "Monthly"),
        ("yearly", "Yearly"),
        ("one_time", "One Time"),
    ]

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="addons"
    )

    name = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    billing_type = models.CharField(
        max_length=20,
        choices=BILLING_TYPE_CHOICES,
        default="monthly",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class SubscriptionAddOn(models.Model):
    subscription = models.ForeignKey(
        "Subscription",
        on_delete=models.CASCADE,
        related_name="subscription_addons"
    )

    addon = models.ForeignKey(
        AddOn,
        on_delete=models.CASCADE
    )

    amount = models.DecimalField(max_digits=10, decimal_places=2)

    is_consumed = models.BooleanField(default=False) 

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.amount:
            self.amount = self.addon.amount
        super().save(*args, **kwargs)
