from django.shortcuts import render
from django.utils import timezone
from django.db.models import Q

from accounts.permissions import permission_denied_response, require_permission
from common.toast_utils import toast_response
from billing.forms import InvoiceForm
from billing.models import Invoice
from subscriptions.models import Subscription


@require_permission("billing.view")
def billing_view(request):
    invoices = Invoice.objects.for_org(request.organization).select_related(
        "subscription", "subscription__customer"
    )

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


@require_permission("billing.create")
def new_invoice(request):
    org = request.organization

    if request.method == "POST":
        form = InvoiceForm(request.POST, organization=org)
        if form.is_valid():
            invoice = form.save(commit=False)
            invoice.organization = org
            invoice.save()
            return toast_response("تم إنشاء الفاتورة بنجاح", type="success")
    else:
        form = InvoiceForm(organization=org, initial={
            "issue_date": timezone.localdate(),
            "due_date": timezone.localdate(),
            "status": "pending",
            "invoice_type": "subscription",
        })

    subscriptions = Subscription.objects.for_org(org).select_related("customer", "plan")

    return render(request, "billing/modal.html", {
        "form": form,
        "subscriptions": subscriptions,
        "today": timezone.localdate(),
    })


@require_permission("billing.edit")
def edit_invoice(request, invoice_id):
    org = request.organization
    invoice = Invoice.objects.for_org(org).filter(id=invoice_id).first()
    if invoice is None:
        return permission_denied_response(request, "billing.edit")

    if request.method == "POST":
        form = InvoiceForm(request.POST, instance=invoice, organization=org)
        if form.is_valid():
            form.save()
            return toast_response("تم تحديث الفاتورة بنجاح", type="success")
    else:
        form = InvoiceForm(instance=invoice, organization=org)

    subscriptions = Subscription.objects.for_org(org).select_related("customer", "plan")

    return render(request, "billing/modal.html", {
        "form": form,
        "invoice": invoice,
        "subscriptions": subscriptions,
        "today": timezone.localdate(),
    })
