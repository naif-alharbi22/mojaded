from django.core.management.base import BaseCommand
from django.utils import timezone
from billing.models import Invoice
from subscriptions.models import Subscription
from datetime import timedelta


class Command(BaseCommand):
    help = "Process subscription renewals"

    def handle(self, *args, **kwargs):
        today = timezone.now().date()

        subscriptions = Subscription.objects.filter(
            status="active",
            next_billing_date__lte=today
        )

        for subscription in subscriptions:
            existing_invoice = Invoice.objects.filter(
            subscription=subscription,
            due_date=subscription.next_billing_date,
            status__in=["pending", "overdue"]
            ).exists()

            if existing_invoice:
                continue
            invoice = subscription.generate_invoice()
            

            subscription.status = "past_due"
            subscription.save()

            self.stdout.write(
                self.style.SUCCESS(
                    f"Invoice created for subscription {subscription.id}"
                )
            )

            grace_period = 7

            overdue_date = today - timedelta(days=grace_period)

            overdue_invoices = Invoice.objects.filter(
                status="pending",
                due_date__lte=overdue_date
            )

            for invoice in overdue_invoices:
                invoice.status = "overdue"
                invoice.save()

                subscription = invoice.subscription
                subscription.status = "past_due"
                subscription.save()

                self.stdout.write(
                    self.style.WARNING(
                        f"Invoice {invoice.id} marked as overdue"
                    )
                )

        self.stdout.write(self.style.SUCCESS("Renewal job completed"))
