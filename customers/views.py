from django.http import HttpResponse
from django.shortcuts import render
from django.db.models import Q
from django.views.decorators.http import require_http_methods
from django.db.models import Q

from common.toast_utils import toast_response
from customers.forms import CustomerForm
from customers.models import Customer


def customers_view(request):
    customers = Customer.objects.for_org(request.organization)

    search_query = request.GET.get("search", "")
    if search_query:
        customers = customers.filter(
            Q(name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query)
        )

    context = {
        "customers": customers,
        "search": search_query,
    }

    if request.headers.get("HX-Request"):
        return render(request, "customers/index.html#content", context)

    return render(request, "customers/index.html", context)


def new_customer(request):
    if request.method == "POST":
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save(commit=False)
            customer.organization = request.organization
            customer.save()
            return HttpResponse(
                "<script>window.dispatchEvent(new Event('customerAdded'));</script>"
            )
    else:
        form = CustomerForm()

    return render(request, "customers/modal.html", {"form": form})


def edit_customer(request, customer_id):
    customer = Customer.objects.for_org(request.organization).get(id=customer_id)

    if request.method == "POST":
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            return toast_response("تم تحديث العميل بنجاح", type="success")
    else:
        form = CustomerForm(instance=customer)

    return render(request, "customers/modal.html", {"form": form})


@require_http_methods(["DELETE"])
def delete_customer(request, customer_id):
    customer = Customer.objects.for_org(request.organization).get(id=customer_id)
    customer.delete()
    return toast_response("تم حذف العميل بنجاح", type="success")
