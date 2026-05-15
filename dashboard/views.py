from datetime import timedelta

from dateutil.relativedelta import relativedelta
from django.db.models import Count, Sum
from django.shortcuts import render
from django.utils import timezone

from activity.models import ActivityLog
from billing.models import Invoice
from customers.models import Customer
from subscriptions.models import Subscription


WEEKDAY_NAMES_AR = [
    "الإثنين", "الثلاثاء", "الأربعاء", "الخميس",
    "الجمعة", "السبت", "الأحد",
]


def _pct_change(current, previous):
    if not previous:
        return None
    return round(((current - previous) / previous) * 100, 1)


def view_dashboard(request):
    org = request.organization
    now = timezone.now()
    today = timezone.localdate()

    this_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_month_start = this_month_start - relativedelta(months=1)

    subs = Subscription.objects.for_org(org)
    customers = Customer.objects.for_org(org)
    invoices = Invoice.objects.for_org(org)

    total_subscriptions = subs.count()
    total_subscriptions_last = subs.filter(created_at__lt=this_month_start).count()

    active_customers = customers.filter(subscriptions__status="active").distinct().count()
    active_customers_last = customers.filter(
        subscriptions__status="active",
        created_at__lt=this_month_start,
    ).distinct().count()

    monthly_revenue = invoices.filter(
        status="paid",
        paid_at__gte=this_month_start,
    ).aggregate(total=Sum("amount"))["total"] or 0

    last_month_revenue = invoices.filter(
        status="paid",
        paid_at__gte=last_month_start,
        paid_at__lt=this_month_start,
    ).aggregate(total=Sum("amount"))["total"] or 0

    current_month_subs = subs.filter(created_at__gte=this_month_start).count()
    last_month_subs_new = subs.filter(
        created_at__gte=last_month_start,
        created_at__lt=this_month_start,
    ).count()

    week_start = today - timedelta(days=6)
    weekly_counts = {
        row["created_at__date"]: row["c"]
        for row in subs.filter(created_at__date__gte=week_start)
        .values("created_at__date")
        .annotate(c=Count("id"))
    }
    recent_logs = (
        ActivityLog.objects
        .filter(org_id=org.id)
        .select_related("user")
        [:8]  # آخر 8 أنشطة بس
    )

    weekly_chart = [
        {
            "label": WEEKDAY_NAMES_AR[(week_start + timedelta(days=i)).weekday()],
            "value": weekly_counts.get(week_start + timedelta(days=i), 0),
        }
        for i in range(7)
    ]

    context = {
        "recent_logs": recent_logs,
        "total_subscriptions": total_subscriptions,
        "total_subscriptions_delta": _pct_change(total_subscriptions, total_subscriptions_last),
        "monthly_revenue": monthly_revenue,
        "monthly_revenue_delta": _pct_change(monthly_revenue, last_month_revenue),
        "active_customers": active_customers,
        "active_customers_delta": _pct_change(active_customers, active_customers_last),
        "current_month_subs": current_month_subs,
        "current_month_subs_delta": _pct_change(current_month_subs, last_month_subs_new),
        "weekly_chart": weekly_chart,
    }

    return render(request, "dashboard/dashboard.html", context)
