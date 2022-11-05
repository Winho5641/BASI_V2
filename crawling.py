import re
import matplotlib.font_manager as fm
import matplotlib.dates as mdates
from urllib.request import urlopen
from PIL import ImageFont
from konlpy.tag import Okt
from wordcloud import WordCloud
from io import BytesIO
import base64
import mpld3
import numpy as np
from bs4 import BeautifulSoup, SoupStrainer
import requests
import datetime
import pandas as pd
from multiprocessing import Pool
import matplotlib.pyplot as plt
from PIL import Image

def href_stock_crawling(link):

    ## 데이터 수집 날짜
    temp_today = datetime.datetime.now()
    temp_yesterday = temp_today - datetime.timedelta(days=7)  ## 원하는 Days(7)동안의 날짜
    today = temp_today.strftime('%Y.%m.%d')  ## 오늘 날짜
    yesterday = temp_yesterday.strftime('%Y.%m.%d')  ## 원하는 날짜 Days(7)

    post_data = []  ## ex) day, time, title, content, good, bad

    ## 현재 해당되는 하이퍼링크 웹크롤링 얻는 데이터 : day, time, title, content, good, bad
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36'}
    html = requests.get(link, headers=headers).content
    strainer = SoupStrainer('table', attrs={'class': 'view'})
    bs_obj = BeautifulSoup(html, "lxml", parse_only=strainer)

    ## 하이퍼링크의 타임라인 (day, time)
    temp_date = bs_obj.find("th", {"class": "gray03 p9 tah"}).text
    post_day = temp_date.split()[0]  ## ex). post_day : 2022.09.25 (현재 게시판의 날짜를 파악하기 위해)
    post_data.append(temp_date.split()[0])  ## ex). day : 2022.09.25
    post_data.append(temp_date.split()[1])  ## ex). time : 14:25

    if (yesterday >= post_day or post_day > today):  ## 수집해야하는 날짜에서 벗어났다면 실행 중단
        return

    ## 하이퍼링크의 제목 (title)
    post_data.append(bs_obj.find("strong", {"class": "c p15"}).text)

    ## 하이퍼링크의 내용 (content)
    temp_content = bs_obj.find("div", {"class": "view_se"}).find_all(text=True)

    content = ''
    for string in temp_content:
        content += string.replace('\r', '').replace('\u3000', '')

    post_data.append(content)

    ## 하이퍼링크의 추천과 비추천 (good, bad)
    post_data.append(int(bs_obj.find("strong", {"class": "tah p11 red01 _goodCnt"}).text))  ## 추천의 수
    post_data.append(int(bs_obj.find("strong", {"class": "tah p11 blue01 _badCnt"}).text))  ## 비추천의 수

    ## 수집데이터(list) Return
    return post_data


def stock_crawling(item):
    ## 데이터 수집 날짜
    temp_today = datetime.datetime.now()
    temp_yesterday = temp_today - datetime.timedelta(days=7)  ## 원하는 Days(7)동안의 날짜
    today = temp_today.strftime('%Y.%m.%d')  ## 오늘 날짜
    yesterday = temp_yesterday.strftime('%Y.%m.%d')  ## 원하는 날짜 Days(7)

    ## 크롤링 데이터 List
    Data = []

    ## 기본 페이지는 1page
    page = '1'



    while (True):  ## Today에서 Yesterday가 될 때까지 반복

        ## 네이버 지식 토론방의 경우는 크롤링을 막아놨기 때문에, 권한을 우회하여 잠시 작동하게 만들었다.
        ## 저작권 법에 의하면 상업적이 아닌 연구 및 개인적인 목적을 위해 크롤링을 하기 때문에 법적으로는 문제가 없다.
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36'}
        url = 'https://finance.naver.com/item/board.naver?code=' + item + '&' + 'page=' + page  ## 네이버 주식 토론방 (item의 토론방)
        html = requests.get(url, headers=headers).content
        strainer = SoupStrainer('table', attrs={'class': 'type2'})
        bs_obj = BeautifulSoup(html, "lxml", parse_only=strainer)

        ## 현재 페이지 추출(href)
        temp_href = bs_obj.select("a")  ## 1페이지의 게시물(20개) 하이퍼링크 (href)

        ## 현재 페이지의 href 배열로 추출
        page_href = []  ## 현재 페이지의 href (총 20개)
        for href in temp_href:
            temp_link = href.attrs['href']

            if ('nid' in temp_link):
                link = "https://finance.naver.com/"
                link += temp_link

                page_href.append(link)

        """
        ## href 웹 크롤링 함수 실행 (Multiprocessing으로 속도 2배이상 개선)
        with Pool(1) as p:
            post_datas = p.map(href_stock_crawling, page_href)  ## Return으로 post 데이터 list 가져옴
        """

        ##TEST
        post_datas = []
        for link in page_href :
            post_datas.append(href_stock_crawling(link))

        return post_datas
        ## 여기까지


        ## 수집된 데이터를 None을 제외하고 데이터 추가
        for p_data in post_datas:
            if (p_data != None):
                Data.append(p_data)

        ## 수집된 데이터에서 None이 있다는 것은 수집해야하는 날짜에서 벗어났다는 뜻이므로 크롤링 종료
        if (None in post_datas):
            return Data

        ## 다음 페이지 전환 (아직 날짜에 벗어나지 않았음)
        page = str(int(page) + 1)

## post count graph 생성
def Count_Graph(days) :

    ## Post Count 계산을 위한 List
    post_count = [0 for _ in range(7)]      ## post count List
    post_day = []                           ## post Day List

    ## post day list 안에 날짜 넣기
    for i in range(6, -1, -1):
        temp_today = datetime.datetime.now()
        temp_postday = temp_today - datetime.timedelta(days=i)
        postday = temp_postday.strftime('%Y.%m.%d')
        post_day.append(postday)

    ## Post Count 실행
    for day in days:
        if (day in post_day):
            post_count[post_day.index(day)] += 1

    post_day = []
    for i in range(6, -1, -1):
        temp_today = datetime.datetime.now()
        temp_postday = temp_today - datetime.timedelta(days=i)
        postday = temp_postday.strftime('%Y.%m.%d')
        post_day.append(datetime.datetime.strptime(postday, '%Y.%m.%d'))

    fig, ax = plt.subplots()

    ax.plot(post_day, post_count, solid_capstyle='round', color='#1F879D', linewidth=2, marker="H")
    #ax.set_xticks(ind)
    #ax.set_xticklabels(post_day)
    dateFmt = mdates.DateFormatter('%Y.%m.%d')
    ax.xaxis.set_major_formatter(dateFmt)
    plt.xticks(post_day)
    plt.yticks(post_count)
    ax.grid(True, alpha=0.1)
    graph = mpld3.fig_to_html(fig)
    return graph

## 불필요 문자 제거 함수
def filter(text) :
    cleaned_text = re.sub('[^가-힣]' , ' ', text)  ## 한글이 아닌 모든 문자 제거
    cleaned_text = re.sub(' +', ' ', cleaned_text) ## 중복된 공백 축소
    return cleaned_text

## title 불용어제거 + 형태소 분석
def title_pos(data):
    ## 불필요 문자 제거
    data['title'] = data['title'].map(filter)

    ## Data에서 제목 추출
    stock_title = data['title']

    okt = Okt()  ## 세종사전 실행하기

    ## 형태소 분석 List 생성
    title_pos = []

    ## 형태소 분석 (title)
    for n in range(0, len(data)):
        morph_title = okt.pos(stock_title[n])
        title_pos.append(morph_title)

    return title_pos

## content 불용어제거 + 형태소 분석
def content_pos(data):
    ## 불필요 문자 제거
    data['content'] = data['content'].map(filter)

    ## Data에서 내용 추출
    stock_content = data['content']

    okt = Okt()  ## 세종사전 실행하기

    ## 형태소 분석 List 생성
    content_pos = []

    ## 형태소 분석 (content)
    for n in range(0, len(data)):
        morph_content = okt.pos(stock_content[n])
        content_pos.append(morph_content)

    return content_pos

## title + content 명사 추출
def Noun_filter(title_pos, content_pos):
    ## 명사 모음 List
    noun_list = []

    ## title의 명사 추출
    for sentence in title_pos:
        for word, tag in sentence:
            if (tag in ["Noun"]):
                noun_list.append(word)

    ## content의 명사 추출
    for sentence in content_pos:
        for word, tag in sentence:
            if (tag in ["Noun"]):
                noun_list.append(word)

    return noun_list

## WordCloud Color
def color_func(word, font_size, position,orientation,random_state=None, **kwargs):
    return("hsl({:d},{:d}%, {:d}%)".format(190, 67, 37))

## word cloud 생성
def Word_Cloud(words) :
    ## word cloud 틀
    custom_mask = np.array(Image.open("home/static/home/css/oval.png"))
    fig, ax = plt.subplots()

    font = 'C:/Users/tooly/AppData/Local/Microsoft/Windows/Fonts/BlackHanSans-Regular.ttf'
    #font = '/usr/share/fonts/truetype/nanum/BlackHanSans-Regular.ttf'
    wordcloud = WordCloud(font_path=font, background_color='white', color_func=color_func, width=1000, height=800,
                          mask=custom_mask,
                          # contour_color='#000000',contour_width=3,  ## 테두리 작업
                          prefer_horizontal=True).generate_from_frequencies(dict(words))
    ax.imshow(wordcloud)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.axis('off')
    plt.axis('off')
    cloud = mpld3.fig_to_html(fig)
    return cloud

def sentiment_score(title_pos, content_pos) :
    sent_dic = pd.read_csv("home/static/home/csv/knu_sentiment_lexicon.csv")

    ## dataframe -> list 변환
    sent_word = np.array(sent_dic['word'].tolist())
    sent_polarity = np.array(sent_dic['polarity'].tolist())

    ## 감성분석을 위한 단어 모음 List (Base는 0으로 시작)
    sent_score = [0 for _ in range(len(title_pos))]

    ## Post = title + content + good + bad
    ## title의 형용사, 동사, 명사에 대한 감성 점수 부여
    n = 0
    for sentence in title_pos:
        for word, tag in sentence:
            if (tag in ["Adjective", "Verb", "Noun"]):
                if (word in sent_word):
                    sent_score[n] += int(sent_polarity[np.where(sent_word == word)])
        n += 1

    ## content의 형용사, 동사, 명사에 대한 감성 점수 부여
    n = 0
    for sentence in content_pos:
        n = 0
        for word, tag in sentence:
            if (tag in ["Adjective", "Verb", "Noun"]):
                if (word in sent_word):
                    sent_score[n] += int(sent_polarity[np.where(sent_word == word)])
        n += 1

    return sent_score

## sentiment pie graph 생성
def Sentiment_graph(pos, neg) :
    ratio = [pos, neg]

    if(pos == 0 and neg == 0) :
        return "감정 데이터가 없습니다."

    labels = ["POSITIVE", "NEGATIVE"]
    group_colors = ['#5199D3', '#EA5C68']
    fig, ax = plt.subplots()

    ax.pie(ratio,
            colors=group_colors,
            textprops={'fontsize': 16, 'weight': 'bold'},
            startangle=270,
            autopct = lambda p: '{:.1f}%'.format(round(p)) if p > 0 else '')
    plt.legend(labels)
    ax.axis('off')

    graph = mpld3.fig_to_html(fig)
    return graph
