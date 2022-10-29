from django.shortcuts import render
from django.views.generic import ListView
from .models import Stock
from django.db.models import Q


def landing(request):
    return render(
        request,
        'home/landing.html'
    )


class StockList(ListView):
    model = Stock

class StockSearch(StockList):
    def get_queryset(self):
        q = self.kwargs['q']
        stock_list = Stock.objects.filter()
        return stock_list

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(StockSearch, self).get_context_data()
        q = self.kwargs['q']
        context['search_info'] = f'{q}의 분석'
        context['data'] = q

        return context

    template_name = 'home/stock_list.html'