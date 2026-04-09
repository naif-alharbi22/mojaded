from django.shortcuts import render
from django.utils import timezone

# Create your views here.

from django.http import HttpResponse

from common.toast_utils import toast_response
from customers.models import Customer
from subscriptions.forms import NewSubscriptionForm, PlanForm
from subscriptions.models import Plan, Subscription

def paywall(request):
    return HttpResponse("حسابك موقوف. تواصل مع الإدارة.")




def account_inactive(request):
    return render(request, "account_inactive.html")

def subscriptions(request):
    subscriptions = Subscription.objects.filter(
        organization=request.user.organization
    ).select_related("customer", "plan")

    search_query = request.GET.get("search", "")

    if search_query:
        subscriptions = subscriptions.filter(
            customer__name__icontains=search_query
        )

    context = {
        "subscriptions": subscriptions,
        "search": search_query,
    }

    if request.headers.get("HX-Request"):
        return render(request, "subscription/index.html#content", context)

    return render(request, "subscription/index.html", context)

def plans_view(request):
    plans = Plan.objects.filter(organization=request.user.organization)

    search_query = request.GET.get("search", "")
    if search_query:
        plans = plans.filter(name__icontains=search_query)

    context = {
        "plans": plans,
        "search": search_query,
    }

    if request.headers.get("HX-Request"):
        return render(request, "plans/index.html#content", context)

    return render(request, "plans/index.html", context)

def new_subscriptions(request):
    if request.method == "POST":
        form = NewSubscriptionForm(request.POST)
        try:
            if form.is_valid():
                subscription = form.save(commit=False)

                # إذا عندك organization من session أو user
                subscription.organization = request.user.organization  # عدلها حسب نظامك

                subscription.save()
                print("POST DATA:", request.POST)
                print("FORM ERRORS:", form.errors)
                print("IS VALID:", form.is_valid())
                # إغلاق المودال بعد النجاح (HTMX)
                return HttpResponse(
                    "<script>window.dispatchEvent(new Event('subscriptionAdded'));</script>"
                )
        except Exception as e:
            form.add_error(None, str(e))
            print("Error creating subscription:", e)
    else:
        form = NewSubscriptionForm(initial={
            "start_date": timezone.localdate(),
            "status": "active",
            "subscription_type": "monthly",
            "duration_months": 1,
        })

    context = {
        "form": form,
        "customers": Customer.objects.all(),
        "plans": Plan.objects.all(),
        "status_choices": Subscription.STATUS_CHOICES,
        "today": timezone.localdate(),
    }

    return render(request, "subscription/modal.html", context)


def new_plan(request):
    if request.method == "POST":
        form = PlanForm(request.POST)
        if form.is_valid():
            plan = form.save(commit=False)
            plan.organization = request.user.organization
            plan.save()
            return toast_response("تم إضافة الباقة بنجاح", type="success")
    else:
        form = PlanForm()

    return render(request, "plans/modal.html", {"form": form})


def edit_plan(request, plan_id):
    plan = Plan.objects.get(id=plan_id, organization=request.user.organization)

    if request.method == "POST":
        form = PlanForm(request.POST, instance=plan)
        if form.is_valid():
            form.save()
            return toast_response("تم تحديث الباقة بنجاح", type="success")
    else:
        form = PlanForm(instance=plan)

    return render(request, "plans/modal.html", {"form": form, "plan": plan})


def edit_subscription(request, subscription_id):
    subscription = Subscription.objects.get(id=subscription_id, organization=request.user.organization)

    if request.method == "POST":
        form = NewSubscriptionForm(request.POST, instance=subscription)
        try:
            if form.is_valid():
                form.save()
                return toast_response("تم تحديث الاشتراك بنجاح", type="success")
        except Exception as e:
            form.add_error(None, str(e))
            print("Error updating subscription:", e)
    else:
        form = NewSubscriptionForm(instance=subscription)

    context = {
        "form": form,
        "customers": Customer.objects.all(),
        "plans": Plan.objects.all(),
        "subscription":subscription,
        "status_choices": Subscription.STATUS_CHOICES,
        "today": timezone.localdate(),
    }

    return render(request, "subscription/modal.html", context)