import pandas as pd
from django.shortcuts import render
from django.views.generic import ListView
from .models import Stock
import datetime
import crawling
from collections import Counter
import numpy as np
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

        ## 크롤링 시작
        AnalyData = crawling.stock_crawling(q)

        ## 데이터 중복 제거
        Analy = list(set([tuple(Arr) for Arr in AnalyData]))

        ## 중복 제거로 인한 순서가 랜덤으로 바뀌어서 정렬
        Analy.sort(key=lambda x: (x[0], x[1]))

        ## 정렬된 데이터 Reverse
        Analy.reverse()

        ## 데이터를 DataFrame으로 전환
        Analy = pd.DataFrame(Analy, columns=["day", "time", "title", "content", "good", "bad"])

        context['Analys'] = Analy

        ## 데이터 수집 날짜
        temp_today = datetime.datetime.now()
        temp_yesterday = temp_today - datetime.timedelta(days=7)  ## 원하는 Days(7)동안의 날짜
        context['today'] = temp_today.strftime('%Y.%m.%d')  ## 오늘 날짜
        context['yesterday'] = temp_yesterday.strftime('%Y.%m.%d')  ## 원하는 날짜 Days(7)

        ## post count graph 함수
        context['Count_graph'] = crawling.Count_Graph(Analy.day)

        ## title, content 불용어제거 + 형태소 분석 실행
        stock_title_pos = crawling.title_pos(Analy)
        stock_content_pos = crawling.content_pos(Analy)

        ## title, content 명사 모음 List
        stock_noun_list = crawling.Noun_filter(stock_title_pos, stock_content_pos)

        ## 추출한 데이터 2글자 이상만 필터링
        stock_noun_list = [n for n in stock_noun_list if len(n) > 1]

        ## 단어별 개수세기
        counts = Counter(stock_noun_list)
        tags = counts.most_common(50)  ## 가장 많은 50개의 명사 추출

        ## Word Cloud 함수
        context['Word_cloud'] = crawling.Word_Cloud(tags)

        sent_score = crawling.sentiment_score(stock_title_pos, stock_content_pos)

        ## Post의 긍정,부정에 따라 Good, Bad 추가 감성 점수 부여
        for i in range(len(Analy)):
            if (sent_score[i] > 0):
                sent_score[i] += Analy.good[i] - Analy.bad[i]
            elif (sent_score[i] < 0):
                sent_score[i] += Analy.bad[i] - Analy.good[i]

        ## 최종 Post 감성 점수의 긍정, 부정 비율
        pos_post = neg_post = 0  ## 긍정 게시물과 부정 게시물 Count
        for score in sent_score:
            if (score > 0):
                pos_post += 1
            elif (score < 0):
                neg_post += 1

        ## Sentiment Pie Graph 함수
        context['Sent_graph'] = crawling.Sentiment_graph(pos_post, neg_post)
        return context

    template_name = 'home/stock_list.html'
