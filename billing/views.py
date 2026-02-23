from django.shortcuts import render
from django.utils import timezone

# Create your views here.

def billing_view(request):
    return render(request, "billing/index.html")

def new_invoices(request):
    today = timezone.localdate().strftime("%Y-%m-%d")
    context = {
        "today": today,
    }
    return render(request, "billing/modal.html", context)