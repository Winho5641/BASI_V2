from django.shortcuts import render
from django.views.generic import ListView
from django.db.models import Q

def landing(request):
    return render(
        request,
        'home/landing.html'
    )
