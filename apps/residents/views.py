import datetime
# pyrefly: ignore [missing-import]
from django.shortcuts import render

# Create your views here.

def add_resident(request):
    return render(request, "residents/add_resident.html")
