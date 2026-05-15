from django.shortcuts import render
from django.utils import timezone
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods

from accounts.permissions import permission_denied_response, require_permission
from common.toast_utils import toast_response
from customers.models import Customer
from subscriptions.forms import NewSubscriptionForm, PlanForm
from subscriptions.models import Plan, Subscription


def paywall(request):
    return HttpResponse("حسابك موقوف. تواصل مع الإدارة.")


def account_inactive(request):
    return render(request, "account_inactive.html")


@require_permission("subscriptions.view")
def subscriptions(request):
    subs = Subscription.objects.for_org(request.organization).select_related("customer", "plan")

    search_query = request.GET.get("search", "")
    status_query = request.GET.get("status", "")

    if search_query:
        subs = subs.filter(customer__name__icontains=search_query)
    
    if status_query:
        subs = subs.filter(status=status_query)

    context = {
        "subscriptions": subs,
        "search": search_query,
        "status": status_query,
    }

    if request.headers.get("HX-Request"):
        return render(request, "subscription/index.html#content", context)

    return render(request, "subscription/index.html", context)


@require_permission("plans.view")
def plans_view(request):
    plans = Plan.objects.for_org(request.organization)

    search_query = request.GET.get("search", "")
    billing_cycle = request.GET.get("billing_cycle", "")

    if search_query:
        plans = plans.filter(name__icontains=search_query)
        
    if billing_cycle:
        plans = plans.filter(billing_cycle=billing_cycle)

    context = {
        "plans": plans,
        "search": search_query,
        "billing_cycle": billing_cycle,
    }

    if request.headers.get("HX-Request"):
        return render(request, "plans/index.html#content", context)

    return render(request, "plans/index.html", context)


@require_permission("subscriptions.create")
def new_subscriptions(request):
    org = request.organization

    if request.method == "POST":
        form = NewSubscriptionForm(request.POST, organization=org)
        if form.is_valid():
            subscription = form.save(commit=False)
            subscription.organization = org
            subscription.save()
            return toast_response("تم إنشاء الاشتراك بنجاح", type="success")
    else:
        form = NewSubscriptionForm(organization=org, initial={
            "start_date": timezone.localdate(),
            "status": "active",
            "subscription_type": "monthly",
            "duration_months": 1,
        })

    context = {
        "form": form,
        "customers": Customer.objects.for_org(org),
        "plans": Plan.objects.for_org(org),
        "status_choices": Subscription.STATUS_CHOICES,
        "today": timezone.localdate(),
    }

    return render(request, "subscription/modal.html", context)


@require_permission("plans.create")
def new_plan(request):
    if request.method == "POST":
        form = PlanForm(request.POST)
        if form.is_valid():
            plan = form.save(commit=False)
            plan.organization = request.organization
            plan.save()
            return toast_response("تم إضافة الباقة بنجاح", type="success")
    else:
        form = PlanForm()

    return render(request, "plans/modal.html", {"form": form})


@require_permission("plans.edit")
def edit_plan(request, plan_id):
    plan = Plan.objects.for_org(request.organization).filter(id=plan_id).first()
    if plan is None:
        return permission_denied_response(request, "plans.edit")

    if request.method == "POST":
        form = PlanForm(request.POST, instance=plan)
        if form.is_valid():
            form.save()
            return toast_response("تم تحديث الباقة بنجاح", type="success")
    else:
        form = PlanForm(instance=plan)

    return render(request, "plans/modal.html", {"form": form, "plan": plan})


@require_permission("subscriptions.edit")
def edit_subscription(request, subscription_id):
    org = request.organization
    subscription = Subscription.objects.for_org(org).filter(id=subscription_id).first()
    if subscription is None:
        return permission_denied_response(request, "subscriptions.edit")

    if request.method == "POST":
        form = NewSubscriptionForm(request.POST, instance=subscription, organization=org)
        if form.is_valid():
            form.save()
            return toast_response("تم تحديث الاشتراك بنجاح", type="success")
    else:
        form = NewSubscriptionForm(instance=subscription, organization=org)

    context = {
        "form": form,
        "customers": Customer.objects.for_org(org),
        "plans": Plan.objects.for_org(org),
        "subscription": subscription,
        "status_choices": Subscription.STATUS_CHOICES,
        "today": timezone.localdate(),
    }

    return render(request, "subscription/modal.html", context)


@require_http_methods(["DELETE"])
@require_permission("subscriptions.delete")
def delete_subscription(request, subscription_id):
    subscription = Subscription.objects.for_org(request.organization).filter(id=subscription_id).first()
    if subscription is None:
        return permission_denied_response(request, "subscriptions.delete")
    subscription.delete()
    return toast_response("تم حذف الاشتراك بنجاح", type="success")


@require_http_methods(["DELETE"])
@require_permission("plans.delete")
def delete_plan(request, plan_id):
    plan = Plan.objects.for_org(request.organization).filter(id=plan_id).first()
    if plan is None:
        return permission_denied_response(request, "plans.delete")
    plan.delete()
    return toast_response("تم حذف الباقة بنجاح", type="success")
