# Create your views here.
from . import TKBapi
import datetime
from django.shortcuts import render

def tkbView(request):
    mtx=TKBapi.getTKB()
    today=datetime.date.today().weekday()
    return render(request, 'TKB.html', {'mtx':mtx, 'day':today})

