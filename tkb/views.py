# Create your views here.
from . import TKBapi
import datetime
from django.shortcuts import render

def tkbView(request):
    mtx, errorCode, errorStr=TKBapi.getTKB()
    today=datetime.date.today().weekday()
    nextDay=(2 if (datetime.datetime.now().hour < 14 or (datetime.datetime.now().hour == 14 and datetime.datetime.now().minute <= 45)) else 3)
    if(today + nextDay > 8):
        today=2
        nextDay=0
    # print(datetime.datetime.now().hour)
    return render(request, 'TKB.html', {'mtx':mtx, 'errcode': errorCode, 'errstr': errorStr, 'day':today + nextDay})

