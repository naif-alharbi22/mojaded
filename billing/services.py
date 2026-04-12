from billing.models import Invoice
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from django.db import transaction


class PaymentError(Exception):
    pass

@transaction.atomic
def create_invoice(subscription):
    return Invoice.objects.create(
        organization=subscription.organization,
        subscription=subscription,
        amount=subscription.total_amount,
        issue_date=timezone.now().date(),
        due_date=subscription.next_billing_date,
    )


@transaction.atomic
def mark_invoice_paid(invoice):

    if invoice.status == "paid":
        raise PaymentError("Invoice already paid")
    
    invoice.status = "paid"
    invoice.paid_at = timezone.now()
    invoice.save()

    subscription = invoice.subscription
    subscription.status = "active"

    if subscription.plan.billing_cycle == "monthly":
        subscription.next_billing_date += relativedelta(months=1)
    elif subscription.plan.billing_cycle == "yearly":
        subscription.next_billing_date += relativedelta(years=1)

    subscription.save()

    return invoice
