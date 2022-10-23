from django.shortcuts import render
from django.views.generic import ListView
from .models import Stock
from django.db.models import Q
import json



def landing(request):
    return render(
        request,
        'home/landing.html'
    )

def stock_list(request):
    names = Stock.objects.all()
    context = {
        "names" : names,
        "names_js" : json.dumps([stock.json() for stock in names])
    }
    return render(request, "landing.html", context)

class StockList(ListView):
    model = Stock

class StockSearch(StockList):
    def get_queryset(self):
        q = self.kwargs['q']
        stock_list = 'None'
        stock_list = Stock.objects.filter(Name=q)
        if(stock_list == 'None'):
            return False
        else :
            return True