from django.shortcuts import render
from django.utils import timezone
from django.db.models import Sum, Count

from subscriptions.models import Subscription
from customers.models import Customer
from billing.models import Invoice


def view_dashboard(request):
    org = request.user.organization
    now = timezone.now()

    total_subscriptions = Subscription.objects.filter(organization=org).count()
    active_customers = Customer.objects.filter(organization=org).count()

    monthly_revenue = Invoice.objects.filter(
        organization=org,
        status="paid",
        paid_at__year=now.year,
        paid_at__month=now.month,
    ).aggregate(total=Sum("amount"))["total"] or 0

    current_month_subs = Subscription.objects.filter(
        organization=org,
        created_at__year=now.year,
        created_at__month=now.month,
    ).count()

    context = {
        "total_subscriptions": total_subscriptions,
        "active_customers": active_customers,
        "monthly_revenue": monthly_revenue,
        "current_month_subs": current_month_subs,
    }

    return render(request, "dashboard/dashboard.html", context)
