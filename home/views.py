import pandas as pd
from django.shortcuts import render
from django.views.generic import ListView
from .models import Stock
import time
import crawling
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


        AnalyData = crawling.stock_crawling(q)
        
        ## 데이터 중복 제거
        Analy = list(set([tuple(Arr) for Arr in AnalyData]))

        ## 중복 제거로 인한 순서가 랜덤으로 바뀌어서 정렬
        Analy.sort(key=lambda x: x[1])

        ## 정렬된 데이터 Reverse
        Analy.reverse()

        ## 데이터를 DataFrame으로 전환
        context['Analys'] = pd.DataFrame(Analy, columns=["day", "time", "title", "content", "good", "bad"])

        ## 데이터 수집 날짜
        temp_today = datetime.datetime.now()
        temp_yesterday = temp_today - datetime.timedelta(days=1)  ## 원하는 Days(2)동안의 날짜
        context['today'] = temp_today.strftime('%Y.%m.%d')  ## 오늘 날짜
        context['yesterday'] = temp_yesterday.strftime('%Y.%m.%d')  ## 원하는 날짜 Days(2)


        return context

    template_name = 'home/stock_list.html'
