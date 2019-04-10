# -*- coding: utf-8 -*-
# describtion: use function request_html_body(url)

__author__ = 'wemiam'

import random
import traceback
import os
import requests
from json import dumps
import jieba
import jieba.analyse
from lxml import html

import time
from bs4 import BeautifulSoup
from Utils.loggerhandler import mylogger
from Utils.loadfile import loadfile


# prepare logger
jobname = os.path.splitext(os.path.basename(__file__))[0]
rootdir = os.path.dirname(os.path.abspath(__file__))
log_path = rootdir + os.path.sep + 'log'
log_file = log_path + os.path.sep + jobname + '.log'
if not os.path.exists(log_path):
    os.makedirs(log_path, 0o775)
logger = mylogger(jobname, log_file)

out_path = rootdir + "/data/"
if not os.path.exists(out_path):
    os.makedirs(out_path, 0o775)

# 无效字段
useless_set = set()
data_path_useless = rootdir + "/data/" + "useless_word.txt"
if os.path.exists(data_path_useless):
    useless_set = loadfile(data_path_useless).as_set()

# 否决字段
reject_list = []
data_path_reject = rootdir + "/data/" + "reject_word.txt"
if os.path.exists(data_path_reject):
    reject_list = loadfile(data_path_reject).as_list()

jieba.set_dictionary(rootdir + '/data/dict.txt.big')
jieba.analyse.set_stop_words(rootdir + '/data/stopwords_zh.txt')


def handle_text_coding(text, coding):
    try:
        if coding.lower() == 'gbk':
            text_encoding = text.encode('iso-8859-1').decode(coding)
        elif not isinstance(text, str):
            text_encoding = text.encode('iso-8859-1').decode(coding)
        else:
            text_encoding = text
        return text_encoding
    except:
        return text


def handle_text_special_symbol(text):
    text_new = text.replace('\t', '').replace('\n', '').replace(' ', '')
    return text_new


def handle_useless_text(text):
    # 低于4位,找到一个无效词的为无效语句
    if len(text) <= 4:
        seg_list = jieba.cut(text , cut_all=False)
        set_target = set(seg_list)
        intersection = list(useless_set.intersection(set_target))
        if len(intersection) >= 1:
            return ''

    # 低于8位,找到两个无效词的为无效语句
    elif len(text) <= 8:
        seg_list = jieba.cut(text, cut_all=False)
        set_target = set(seg_list)
        intersection = list(useless_set.intersection(set_target))
        if len(intersection) >= 2:
            return ''

    # 低于30位,综合无效词出现的次数判断
    elif len(text) <= 30:
        seg_list = jieba.cut(text , cut_all=False)
        set_target = set(seg_list)

        tags = jieba.analyse.extract_tags(text, topK=10)
        set_tags = set(tags)

        intersection = list(useless_set.intersection(set_target))
        suspicious = len(intersection) / len(tags)

        if len(intersection) >= 1 and suspicious > 0.32:
            return ''

    return text


def handle_reject_text(text):
    for reject_str in reject_list:
        if text.find(reject_str) != -1:
            return ""
    return text


def handle_text(text, coding):
    try:
        text = handle_text_coding(text, coding)
        #text = handle_text_special_symbol(text)
        text = handle_useless_text(text)
        text = handle_reject_text(text)
        return text
    except:
        logger.error('handle text error: {}'.format(text))
        return text


def handle_page(content, url, apparent_encoding):

    try:
        if apparent_encoding == 'utf-8':
            content = content.decode(apparent_encoding)
        soup = BeautifulSoup(content, 'html5lib')
        #html title
        html_title = soup.find("title")
        title_text = handle_text(html_title.text, apparent_encoding)

        #html body
        p_list = []
        span_list = []

        #all p tags
        html_p_list = soup.find_all("p")
        for html_p in html_p_list:
            p_text = handle_text(html_p.text, apparent_encoding)
            if p_text != "":
                p_list.append(p_text)

        #all span tags
        if len(p_list) == 0:
            html_span_list = soup.find_all("span")
            for html_span in html_span_list:
                span_text = handle_text(html_span.text , apparent_encoding)
                if span_text != "":
                    span_list.append(span_text)
            p_list = span_list

        res = {
            "title": title_text,
            "url": url,
            "p_list": p_list
        }

        return res
    except Exception:
        logger.error("Unexpected error: {}".format(traceback.format_exc()))


def request_html_body(url):

    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-encoding": "gzip, deflate",
        "Accept-language": "zh-CN",
        "Connection": 'close',
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/11.1 Safari/605.1.15",
    }

    logger.info('start request: {}'.format(url))
    response = requests.get(url, headers=headers, timeout=10)
    res = handle_page(response.content, url, response.apparent_encoding)
    return res


def request_and_save_page(url):

    res = request_html_body(url)
    res_str = dumps(res)

    file_name = res['title'][0:20].replace('/', '')
    out_file = out_path + os.path.sep + file_name + '.txt'
    f = open(out_file, 'w')
    f.write(res_str)
    f.flush()
    f.close()


def request_page_api(url):
    return request_html_body(url)


def test():
    url_list = [
        'https://blog.csdn.net/TCF_JingFeng/article/details/80801079',
        'http://news.163.com/18/0625/09/DL4SBKLP0001875O.html',
        'http://news.sina.com.cn/gov/xlxw/2018-06-25/doc-ihencxtt8123388.shtml',
        'https://mbd.baidu.com/newspage/data/landingsuper?context=%7B%22nid%22%3A%22news_9594549139297983511%22%7D&n_type=0&p_from=1',
        'http://news.163.com/18/0626/10/DL7IURID0001875P.html',
        'http://news.163.com/18/0626/13/DL7S0K170001875N.html',
        'http://new.qq.com/cmsn/NEW20180/NEW2018062600277603.html',
        'http://new.qq.com/omn/20180626/20180626A06Y0V.html',
        'http://wanmeishijiexiaoshuo.org/book/1055.html',
        'http://wanmeishijiexiaoshuo.org/book/1057.html',
        'http://blog.sina.com.cn/s/blog_49818dcb0102ypur.html',
        'http://blog.sina.com.cn/s/blog_15f20fe440102xk30.html',
        'http://blog.sina.com.cn/s/blog_56c35a550102y9gc.html',
        'http://mzs1973.blog.163.com/blog/static/369786202017716114054665/?touping',
        'https://www.apple.com/cn/shop/help/returns_refund',
        'https://www.cnblogs.com/sleeping-cat/p/9224335.html',
        'https://mbd.baidu.com/newspage/data/landingsuper?context=%7B%22nid%22%3A%22news_7336857484879626542%22%7D&n_type=0&p_from=1',
        'https://mbd.baidu.com/newspage/data/landingsuper?context=%7B%22nid%22%3A%22news_16004330066448942281%22%7D&n_type=0&p_from=1'
    ]
    for url in url_list:
        result = request_html_body(url)
        print(result)



if __name__ == "__main__":

    test_url = "https://www.mafengwo.cn/i/9941058.html"
    res = request_html_body(test_url)
    print(res)