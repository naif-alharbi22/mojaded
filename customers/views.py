from django.http import HttpResponse
from django.shortcuts import render

from customers.forms import CustomerForm
from customers.models import Customer
from django.db.models import Q


# Create your views here.


def customers_view(request):
    template_name = "customers/index.html"

    customers = Customer.objects.filter(
        organization=request.user.organization
    )

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

    # 👇 هذا أهم جزء
    if request.headers.get("HX-Request"):
        return render(request, "customers/index.html#content", context)

    return render(request, template_name, context)

def new_customer(request):
    if request.method == "POST":
        form = CustomerForm(request.POST)

        if form.is_valid():
            customer = form.save(commit=False)
            customer.organization = request.user.organization
            customer.save()

            return HttpResponse(
                "<script>window.dispatchEvent(new Event('customerAdded'));</script>"
            )
    else:
        form = CustomerForm()

    return render(request, "customers/modal.html", {"form": form})