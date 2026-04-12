from django.shortcuts import render
from django.utils import timezone
from django.db.models import Sum

from subscriptions.models import Subscription
from customers.models import Customer
from billing.models import Invoice


def view_dashboard(request):
    org = request.organization
    now = timezone.now()

    total_subscriptions = Subscription.objects.for_org(org).count()
    active_customers = Customer.objects.for_org(org).count()

    monthly_revenue = Invoice.objects.for_org(org).filter(
        status="paid",
        paid_at__year=now.year,
        paid_at__month=now.month,
    ).aggregate(total=Sum("amount"))["total"] or 0

    current_month_subs = Subscription.objects.for_org(org).filter(
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
