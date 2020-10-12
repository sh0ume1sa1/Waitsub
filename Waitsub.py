r"""
wait sub
search sub of jpn on opensubtitile.org
menu:
1. add a new movie
2. list sub
"""

__author__ = 'sai.sm'


from bs4 import BeautifulSoup
# -*- coding: utf-8 -*-
import urllib.request
import requests
import json
import datetime
import sys
import re
import logging
import codecs
from smtplib import SMTP_SSL
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import datetime

SUB_DL_DIR = "..\\sub"
RESOURCE = "./res/resource.json"
# opensubtile
COMMON_HEAD = "https://www.opensubtitles.org/en/"
SUB_URL_FORSEARCH_JP = "https://www.opensubtitles.org/libs/suggest.php?format=json3&MovieName=TESTTEST&SubLanguageID=jpn"
#todo SUB_URL_FORSEARCH_ZH = "https://www.opensubtitles.org/libs/suggest.php?format=json3&MovieName=TESTTEST&SubLanguageID=jpn"
SUB_URL = COMMON_HEAD + "subtitleserve/sub/SUBID"
SUB_DL_URL = COMMON_HEAD + "download/sub/SUBID"
MOVIE_URL_JP = "search/sublanguageid-jpn/idmovie-MOVIEID"
DL_URL = "http://dl.opensubtitles.org/en/download/sub/"
DEBUG = False
IDM =" idman.exe /n /p b:\ /d "
MAIL = """\
<html>
  <head></head>
  <body>
    <h1>字幕</h1>
    <ul>
        {}
    </ul>
  </body>
</html>
"""
SUB_MAIL ="""\
    <li>
    <p id="movie2001">{}</p>
    <img width="94" height="139" id="coverurl" src="{}" />
    <p id="subname">{}</p>
    <p id="dlurl">  {} </p>
    <p>Rate: {} @ {}</p>
    </p>
    </li>
"""

class Subtitle():
    movie_title = ""
    movie_year = ""
    sub_url_forsearch = ""
    sub_file_name = []
    movie_target = []
    debug = False

    @classmethod
    def __init__(cls, movie_title, movie_year=''):
        cls.movie_title = movie_title
        cls.movie_year = movie_year
        cls.sub_url_forsearch = SUB_URL_FORSEARCH_JP.replace('TESTTEST', cls.movie_title.replace(' ', '%20'))

    @classmethod
    def set_movie_object(cls, movie_info):
        movie_object =  {
            "key": cls.movie_title,
            "id": "",
            "cover":"",
            "name": '',
            "year": '',
            "wanted": True,
            "movie_url": MOVIE_URL_JP,
            "found": False,
            "total": 0,
            "lastFound": "",
            "subList": [],
            "subListFlat" :"",
            "subListHtml" :""
        }
        if (movie_info != []):
            movie_object['id'] = movie_info['name']+'-'+movie_info['year']
            movie_object['name'] = movie_info['name']
            movie_object['year'] = movie_info['year']
            movie_object['movie_url'] = movie_object['movie_url'].replace(
                'MOVIEID', str(movie_info['id']))
            movie_object['found'] = True
            movie_object['total'] = movie_info['total']
            movie_object['lastFound'] = str(datetime.date.today())
            movie_object['subList'] = cls.get_sub_info(movie_object)
            for f in movie_object['subList']:
                movie_object['subListHtml']+=(SUB_MAIL.format(movie_object['key']+movie_object['year'],f['cover'],f['subName'],f['subUrl'],f['rating'],f['uploadYmd']))
                #movie_object['subListFlat']+=f['subName']+" rating:"+f['rating']+" year:"+f['uploadYmd']+" "+f['cover']+"  "+f['subUrl']
        cls.movie_target.append(movie_object)

    @classmethod
    def get_movie_info(cls):
        try:
            r_get = requests.get(cls.sub_url_forsearch)
            movies_info = json.loads(r_get.text)
            # _print(movies_info)
            cls.movie_target = []
            for movie_info in movies_info:
                if (cls.movie_year == '' or cls.movie_year != '' and movie_info['year'] == cls.movie_year):
                    cls.set_movie_object(movie_info)

        except Exception as e:
            logging.exception(e)

    # scratch core
    @classmethod
    def get_sub_info(cls, movie_object):
        rtn = []
        movie_url = movie_object['movie_url']
        print(movie_object['name'], movie_object['total']+' subs')
        html = urllib.request.urlopen(COMMON_HEAD+movie_url).read()
        soup = BeautifulSoup(html, 'html.parser')
        # 一つ以上字幕があった場合
        if int(movie_object['total']) > 1:
            # cover url
            sub_img=""
            for cover in soup.find_all('img',title=' - subtitles'):
                if cover!= None:
                    sub_img = 'https:'+cover['src']
            all_sub = soup.find_all('tr', id=re.compile(r'^name\d{3,9}$'))
            # print(all_sub)
            for one_sub in all_sub:
                sub_id = one_sub.find_all('td')[0]['id'].replace('main', '')
                subName = one_sub.find_all('td')[0].text.replace(
                    'Watch onlineDownload Subtitles Searcher', '')
                uploadYmd = one_sub.find_all(
                    'td')[3].find('time').text.split("/")
                #subUrl = one_sub.find_all('td')[4].find('a')['href']
                subUrl = SUB_DL_URL.replace('SUBID', sub_id)
                try:
                    rating = one_sub.find_all('td')[5].find(
                        'span').text + '/' + one_sub.find_all('td')[5].find('span')['title']
                except:
                    rating = "解析error"
                single_sub = {
                    "subId": sub_id,
                    "subName": subName,
                    "rating": rating,
                    "uploadYmd": uploadYmd[2]+'/'+uploadYmd[1]+'/'+uploadYmd[0],
                    "subUrl": subUrl,
                    "cover": sub_img
                }
                # print(single_sub)
                rtn.append(single_sub)
        else:
            # only one subtitile, html rendered differently
            sub_id = soup.find('a', download='download')['data-product-id']
            sub_img= ''
            #subUrl = soup.find('a',download='download')['href']
            subUrl = SUB_DL_URL.replace('SUBID', sub_id)
            for cover in soup.find_all('a',title='Download'):
                u = cover.find('img')
                if u!= None:
                    sub_img = 'https:'+u['src']
  

            subName = soup.find('a', download='download')['data-product-name']
            single_sub = {
                "subId": sub_id,
                "subName": subName,
                "rating": 'N/A',
                "uploadYmd": 'N/A',
                "subUrl": subUrl,
                "cover":sub_img
            }
            rtn.append(single_sub)
        # print(rtn)
        return rtn

def send_mail(mail_info):
    mail_to = mail_info['mail_to']
    mail_server = mail_info["mail_server"]
    mail_port = mail_info["mail_port"]
    mail_user = mail_info["mail_user"]
    mail_subject = mail_info["mail_subject"]+(datetime.datetime.now().strftime('%Y/%m/%d'))
    mail_pass = mail_info["mail_pass"]
    mail_body = mail_info["mail_body"]
    
    try:
        with SMTP_SSL(host=mail_server, port=mail_port, local_hostname=None, timeout=3000, source_address=None) as smtpobj:
            msg = MIMEMultipart('alternative')
            msg.set_charset("shift-js")
            msg.add_header('from', mail_user)
            msg.add_header('To',', '.join(mail_to))
            msg.add_header('subject',mail_subject)
            print(mail_subject)
            msg.attach(MIMEText(MAIL.format(mail_body),'html'))
            smtpobj.set_debuglevel(1)
            smtpobj.login(mail_user, mail_pass)
            smtpobj.send_message(msg)
            #smtpobj.sendmail('caijmiscool@gmail.com', mail_server, msg.as_string())
            
            smtpobj.quit()
    except Exception as e:
        logging.exception(e)

if __name__ == '__main__':
    args = sys.argv
    if len(args) <= 2:
        #print("usage : python Waitsub.py movie-name [movie-year]")
        resource_json_file = codecs.open(RESOURCE, 'r','utf-8')
        resource_json = json.load(resource_json_file)
        mail_info = resource_json['mail_info']
        # search subtitles
        mail_body = ""
        has_result = False
        for m in resource_json['moveie_for_search']:
                if (m['wanted']):
                    sub = Subtitle(m['name'], m['year'])
                    sub.get_movie_info()
                    #print(sub.movie_target)
                    if (sub.movie_target != []):
                        has_result = True
                        for t in sub.movie_target:
                            mail_body += t['subListHtml']+"\n"
                    else:
                        mail_body += "  no jap subtitle found\n"
                        print(m['name']+"("+ m['year']+") has no results")
        mail_info['mail_body'] = mail_body
        if (len(args)  == 2 and has_result): #password inputed and subtitle found
            mail_info["mail_pass"] = args[1]
            send_mail(mail_info)
        else:
            if (mail_body != ''):
                print("--------------------\n")
                print(mail_body)
        resource_json_file.close()
    else:
        #mail test
        print("usage: python Waitsub.py or python Waitsub.py mailpassword(for sending mail)")