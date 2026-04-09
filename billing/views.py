from django.shortcuts import render
from django.utils import timezone
from django.db.models import Q

from common.toast_utils import toast_response
from billing.forms import InvoiceForm
from billing.models import Invoice
from subscriptions.models import Subscription


def billing_view(request):
    invoices = Invoice.objects.filter(
        organization=request.user.organization
    ).select_related("subscription", "subscription__customer")

    search_query = request.GET.get("search", "")
    if search_query:
        invoices = invoices.filter(
            Q(subscription__customer__name__icontains=search_query) |
            Q(id__icontains=search_query)
        )

    context = {
        "invoices": invoices,
        "search": search_query,
    }

    if request.headers.get("HX-Request"):
        return render(request, "billing/index.html#content", context)

    return render(request, "billing/index.html", context)


def new_invoice(request):
    if request.method == "POST":
        form = InvoiceForm(request.POST)
        if form.is_valid():
            invoice = form.save(commit=False)
            invoice.organization = request.user.organization
            invoice.save()
            return toast_response("تم إنشاء الفاتورة بنجاح", type="success")
    else:
        form = InvoiceForm(initial={
            "issue_date": timezone.localdate(),
            "due_date": timezone.localdate(),
            "status": "pending",
            "invoice_type": "subscription",
        })

    subscriptions = Subscription.objects.filter(
        organization=request.user.organization
    ).select_related("customer", "plan")

    return render(request, "billing/modal.html", {
        "form": form,
        "subscriptions": subscriptions,
        "today": timezone.localdate(),
    })


def edit_invoice(request, invoice_id):
    invoice = Invoice.objects.get(id=invoice_id, organization=request.user.organization)

    if request.method == "POST":
        form = InvoiceForm(request.POST, instance=invoice)
        if form.is_valid():
            form.save()
            return toast_response("تم تحديث الفاتورة بنجاح", type="success")
    else:
        form = InvoiceForm(instance=invoice)

    subscriptions = Subscription.objects.filter(
        organization=request.user.organization
    ).select_related("customer", "plan")

    return render(request, "billing/modal.html", {
        "form": form,
        "invoice": invoice,
        "subscriptions": subscriptions,
        "today": timezone.localdate(),
    })
