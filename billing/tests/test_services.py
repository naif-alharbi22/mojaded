from django.test import TestCase
from django.utils import timezone
from dateutil.relativedelta import relativedelta

from organizations.models import Organization
from customers.models import Customer
from subscriptions.models import Plan, Subscription
from billing.models import Invoice
from billing.services import mark_invoice_paid
from django.contrib.auth import get_user_model
from billing.services import mark_invoice_paid, PaymentError

User = get_user_model()

class MarkInvoicePaidTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass"
        )

        self.organization = Organization.objects.create(
            name="Test Org",
            slug="test-org",
            status="active",
            owner=self.user   
        )

        self.customer = Customer.objects.create(
            organization=self.organization,
            name="Test Customer"
        )

        self.plan = Plan.objects.create(
            organization=self.organization,
            name="Basic Plan",
            amount=100,
            billing_cycle="monthly"
        )

        self.subscription = Subscription.objects.create(
            organization=self.organization,
            customer=self.customer,
            plan=self.plan,
            start_date=timezone.now().date(),
        )

        self.invoice = Invoice.objects.create(
            organization=self.organization,
            subscription=self.subscription,
            amount=100,
            due_date=self.subscription.next_billing_date
        )

    def test_mark_invoice_paid_updates_invoice_and_subscription(self):
        old_next_date = self.subscription.next_billing_date

        mark_invoice_paid(self.invoice)

        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, "paid")
        self.assertIsNotNone(self.invoice.paid_at)

        self.subscription.refresh_from_db()
        self.assertEqual(self.subscription.status, "active")
        self.assertEqual(
            self.subscription.next_billing_date,
            old_next_date + relativedelta(months=1)
        )
    
    def test_cannot_pay_invoice_twice(self):

        mark_invoice_paid(self.invoice)

        self.invoice.refresh_from_db()
        self.subscription.refresh_from_db()

        old_next_date = self.subscription.next_billing_date

        with self.assertRaises(PaymentError):
            mark_invoice_paid(self.invoice)

        self.subscription.refresh_from_db()
        self.assertEqual(self.subscription.next_billing_date, old_next_date)



