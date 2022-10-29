from urllib.request import urlopen
from bs4 import BeautifulSoup, SoupStrainer
import requests
import datetime
import pandas as pd
from multiprocessing import Pool


def href_stock_crawling(link):
    ## 전역변수 오늘 날짜, 어제 날짜 가져오기
    global today, yesterday

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
    ## 전역변수 오늘 날짜, 어제 날짜, 데이터 가져오기
    global today, yesterday, Data

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

        ## href 웹 크롤링 함수 실행 (Multiprocessing으로 속도 2배이상 개선)
        with Pool(5) as p:
            post_datas = p.map(href_stock_crawling, page_href)  ## Return으로 post 데이터 list 가져옴

        ## 수집된 데이터를 None을 제외하고 데이터 추가
        for p_data in post_datas:
            if (p_data != None):
                Data.append(p_data)

        ## 수집된 데이터에서 None이 있다는 것은 수집해야하는 날짜에서 벗어났다는 뜻이므로 크롤링 종료
        if (None in post_datas):
            return

        ## 다음 페이지 전환 (아직 날짜에 벗어나지 않았음)
        page = str(int(page) + 1)


## 오늘 날짜와 어제 날짜 구하기 (전역변수)
temp_today = datetime.datetime.now()
temp_yesterday = temp_today - datetime.timedelta(days=2)  ## 원하는 Days(2)동안의 날짜
today = temp_today.strftime('%Y.%m.%d')  ## 오늘 날짜
yesterday = temp_yesterday.strftime('%Y.%m.%d')  ## 원하는 날짜 Days(2)
Data = []  ## 크롤링 데이터 List

## 메인 함수
if __name__ == '__main__':
    ## 종목 코드
    item_list = ['122630']

    ## 크롤링 함수
    stock_crawling(item_list[0])

    ## 데이터 중복 제거
    Data = list(set([tuple(Arr) for Arr in Data]))

    ## 중복 제거로 인한 순서가 랜덤으로 바뀌어서 정렬
    Data.sort(key=lambda x: x[1])

    ## 정렬된 데이터 Reverse
    Data.reverse()

    ## 데이터를 DataFrame으로 전환
    df = pd.DataFrame(Data, columns=["day", "time", "title", "content", "good", "bad"])
