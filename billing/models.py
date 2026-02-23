from django.db import models
from django.utils import timezone
from dateutil.relativedelta import relativedelta



class Invoice(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("overdue", "Overdue"),
        ("cancelled", "Cancelled"),
    ]
    INVOICE_TYPE = [
    ("subscription", "Subscription"),
    ("manual", "Manual"),
    ("adjustment", "Adjustment"),
]

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="invoices"
    )
    invoice_type = models.CharField(
        max_length=20,
        choices=INVOICE_TYPE,
        default="subscription"
    )


    subscription = models.ForeignKey(
        "subscriptions.Subscription",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="invoices"
    )

    amount = models.DecimalField(max_digits=10, decimal_places=2)

    issue_date = models.DateField(default=timezone.now)
    due_date = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    paid_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def mark_as_paid(self):
        self.status = "paid"
        self.paid_at = timezone.now()
        self.save()

        subscription = self.subscription
        subscription.status = "active"

        if subscription.plan.billing_cycle == "monthly":
            subscription.next_billing_date += relativedelta(months=1)
        elif subscription.plan.billing_cycle == "yearly":
            subscription.next_billing_date += relativedelta(years=1)

        subscription.save()
