from django.db import models
from organizations.models import Organization
from customers.models import Customer
from dateutil.relativedelta import relativedelta
from billing.models import Invoice
from django.utils import timezone


class Plan(models.Model):
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
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    billing_cycle = models.CharField(
        max_length=10,
        choices=BILLING_CYCLE_CHOICES,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Subscription(models.Model):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("past_due", "Past Due"),
        ("cancelled", "Cancelled"),
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

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="active",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    note = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.amount and self.plan:
            self.amount = self.plan.amount

        if not self.next_billing_date and self.plan and self.start_date:
            if self.plan.billing_cycle == "monthly":
                self.next_billing_date = self.start_date + relativedelta(months=1)
            elif self.plan.billing_cycle == "yearly":
                self.next_billing_date = self.start_date + relativedelta(years=1)

        super().save(*args, **kwargs)

    def generate_invoice(self):
        return Invoice.objects.create(
            organization=self.organization,
            subscription=self,
            amount=self.total_amount,
            issue_date=timezone.now().date(),
            due_date=self.next_billing_date,
        )

    
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
