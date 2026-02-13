from django.shortcuts import render

# Create your views here.

from django.http import HttpResponse

def paywall(request):
    return HttpResponse("حسابك موقوف. تواصل مع الإدارة.")




def account_inactive(request):
    return render(request, "account_inactive.html")

def subscriptions(request):
    return render(request, "subscription/index.html")