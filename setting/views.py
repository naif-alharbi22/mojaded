from django.shortcuts import render

# Create your views here.


def view_settings(request):
    return render(request, "setting/index.html")