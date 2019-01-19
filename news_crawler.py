import requests, datetime
from bs4 import BeautifulSoup
from random import randint

title = []
href = []
image_ref = []
author = []
date = []
default_img = 'file//location/'

def article_info_scraper(arefs):
    for link in arefs:
        source = requests.get(link)
        soup = BeautifulSoup(source.text, features="lxml")

        info_type = [{'class':'author_top'},{'id':'article_date'}]

        index = 0
        while index < len(info_type):
            for list in soup.find_all('div',info_type[index]):
                if index == 0:
                    author.append(list.span.text)
                else:
                    dformatres = list.span.get_text(strip=True).replace('Published','Published ')
                    dformatres = dformatres.replace('Last reviewed', 'Last reviewed ')
                    date.append(dformatres)
            index += 1

def article_header_spider_md(max_pages, limiter=3):
    page_no = 1

    while page_no <= max_pages:
        url = 'https://www.news-medical.net/medical/news?page=' + str(page_no)
        source = requests.get(url)
        soup = BeautifulSoup(source.text, features="lxml")

        article_type = ['thumb big-thumb','thumb small-thumb thumb-right']

        for meta in soup.findAll('span',{'class':'article-meta-date'}, limit=limiter):
            date.append(meta.get_text(strip=True))

        index = 0
        while index < len(article_type):
            for col in soup.findAll('div',{'class':article_type[index]}, limit=limiter-1):
                img_attr = col.findChildren('a')
                href.append('https://www.news-medical.net'+col.a['href'])
                for a in img_attr:
                    title.append(a.img['title'])
                    image_ref.append(a.img['src'])
            index += 1
        page_no += 1


def article_header_spider_health(max_pages, limiter=3):
    page_no = 1

    while page_no <= max_pages:
        url = 'http://www.pna.gov.ph/categories/health-and-lifestyle?page=' + str(page_no)
        source = requests.get(url)
        soup = BeautifulSoup(source.text, features="lxml")

        for heading in soup.findAll('h3',{'class':'media-heading'},limit=limiter):
            title.append(heading.a.text)
            href.append('http://www.pna.gov.ph'+heading.a['href'])
        for cal in soup.findAll('p',{'class':'byline'},limit=limiter):
            date.append(cal.get_text(strip=True))
        for article in soup.findAll('div',{'class':'article media'},limit=limiter):
            image = article.find('img')
            image_ref.append(image['src'] if image else default_img)

        page_no += 1


def article_header_spider_today(max_pages, limiter=3):
    page_no = 1

    while page_no <= max_pages:
        url = 'https://www.medicalnewstoday.com/'
        source = requests.get(url)
        soup = BeautifulSoup(source.text, features="lxml")

        headline_types = ['headlines_fresh','headlines_split']
        article_types = ['featured','written','spotlight','knowledge']

        headline_index = 0
        while headline_index < len(headline_types):
            for fresh_headlines in soup.findAll('div',{'class':headline_types[headline_index]}):
                article_index = 0
                while article_index < len(article_types):
                    for article in fresh_headlines.findChildren('li',{'class':article_types[article_index]}):
                        if len(title) < limiter: title.append(article.a['title'])
                        if len(href) < limiter: href.append(url+article.a['href'])
                        image = article.findChildren('img')
                        for img in image:
                            if len(image_ref) < limiter: image_ref.append(img['data-src'])
                    article_index+=1
            headline_index+=1
        year_now = datetime.datetime.now().year
        for overall_date in soup.findAll('div',{'class':'datebox'}):
            month = overall_date.find('span',{'class':'month'})
            day = overall_date.find('span',{'class':'day'})
            for i in range(limiter):
                date.append('%s %s, %s' % (month.text, day.text, year_now))

        page_no += 1


def get_articles(count):

    article_header_spider_today(count)
    article_header_spider_md(1)
    article_header_spider_health(count)
    newsStr = ""
    for i in range(count*3):
    	newsStr += title[i]+"-/-"+href[i]+"-/-"+image_ref[i]+"-/-"+date[i]+"-/-"

    return newsStr
