from django.shortcuts import render
from django.utils import timezone

# Create your views here.

def billing_view(request):
    return render(request, "billing/index.html")

