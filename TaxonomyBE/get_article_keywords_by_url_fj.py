#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import random
import sys
import time

import jieba

try:
    import cPickle as pk
except:
    try:
        import _pickle as pk
    except:
        import pickle as pk
import pandas as pd
import numpy as np
import zhconv
import traceback
from time import strftime
from collections import defaultdict, Counter
from get_html_content import request_page_api
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from gensim.models import Word2Vec
#from enrich_article_keywords import get_similarities
from Utils.loadfile import loadfile
from Utils.loggerhandler import mylogger
import re


def check_version():
    if sys.version_info < (3, 0):
        sys.stdout.write('Please use python 3.x to run this script!\n')
        sys.exit(255)


check_version()

file = open("/Users/mafeipeng/Desktop/result","w", 1)


# prepare logger
jobname = os.path.splitext(os.path.basename(__file__))[0]
rootdir = os.path.dirname(os.path.abspath(__file__))
log_path = rootdir + os.path.sep + 'log'
log_file = log_path + os.path.sep + jobname + '.log'
if not os.path.exists(log_path):
    os.makedirs(log_path, 0o775)
logger = mylogger(jobname, log_file)

# define constants
m_path = rootdir + '/data/model_zh/2018-07-02.model.word2vec_gensim'
#m = Word2Vec.load(m_path)

# make sure dir exist
def __makesuredirexist__(path):
    if not os.path.exists(path):
        logger.warning('path does not exist: {}'.format(path))
        logger.warning('auto create {}'.format(path))
        os.makedirs(path, 0o775)


# make sure file exist
def __makesurefileexist__(path):
    if not os.path.exists(path):
        logger.warning('path does not exist: {}'.format(path))
        logger.warning('auto create {}'.format(path))
        open(path, 'w').close()


# 中文去停用词
jieba.set_dictionary(rootdir + '/data/dict.txt.big')
stopwords = pd.read_csv(rootdir + '/data/stopwords_zh.txt', index_col=False, quoting=3, sep="\t", names=['stopword'],
                        encoding='utf-8')
stopwords = stopwords['stopword'].values


def preprocess_text(content_lines, sentences):
    for line in content_lines:
        try:
            segs = jieba.lcut(line)
            segs = filter(lambda x: len(x) > 1, segs)
            segs = filter(lambda x: x not in stopwords, segs)
            sentences.append(" ".join(segs))
        except Exception:
            print(line)
            continue

def takeSecond(elem):
    return elem[1]

def get_paragraphs(url):
    p_list = []
    url = url.replace('\n', '')
    logger.debug('start request:' + url)
    res = request_page_api(url)
    if 'p_list' in res:
        p_list = res.get('p_list')
    logger.debug(res)
    logger.debug('end request')
    time.sleep(random.randint(1, 2))
    return p_list

# 取文章关键词
def get_tagging_words(paragraphs, verbose=False):
    words = set()
    # tagging start
    logger.info('tagging start')
    tagging = pd.DataFrame({'snippets': paragraphs})
    collect_snippet_stat = defaultdict(list)
    snippet_count = defaultdict(set)
    snippet_count2 = defaultdict(set)
    snippet_tags_kwds_cnt = Counter()

    for i, p in enumerate(paragraphs):
        snippets = [zhconv.convert_for_mw(p, 'zh-cn')]
        sentences = []
        preprocess_text(snippets, sentences=sentences)
        collect_snippet_stat[i] = sentences
        snippet_cnt_vectorizer = CountVectorizer()
        try:
            snippet_cnt = snippet_cnt_vectorizer.fit_transform(collect_snippet_stat[i])
            # snippet_tags for p
            snippet_count[i].update(
                np.array(snippet_cnt_vectorizer.get_feature_names())[snippet_cnt.toarray().sum(axis=0) > 0])
            snippet_tags_kwds_cnt.update(snippet_count[i])
            snippet_tags_kwds_cnt.update(snippet_count2[i])
        except:
            snippet_count[i].update([])
            snippet_count2[i].update([])



    # tagging snippet_tags
    tagging['snippet_tags'] = tagging.apply(lambda x: snippet_count[x.name], axis=1)

    # tagging snippet_tags_stat2
    valid_wd = list([(k, v) for k, v in snippet_tags_kwds_cnt.items() if (1 < v <= 20)])
    tagging['snippet_tags_stat2'] = tagging.apply(lambda x: snippet_count2[x.name].intersection(valid_wd), axis=1)

    valid_wd.sort(key=takeSecond, reverse=True)

    pattern = re.compile(r'[a-z0-9A-Z_]')

    result = list(k for k, v in valid_wd if len(re.findall(pattern, k)) == 0)
    print(valid_wd)


    for k, v in valid_wd:
        file.write("%s," % k)
        file.write("%s\n" % v)


    # tagging end
    logger.info('tagging end')
    if verbose:
        tagging.drop(labels=['snippets'], axis=1, inplace=True, errors='ignore')
        tagging.to_csv(outfile + '.' + strftime('%Y-%m-%d_%H%M%S') + '.tagging', encoding='utf-8')

    # collect words from tagging result
    #tagging['snippet_tags'].apply(lambda x: words.update(x))

    return result



def main():

    url_list = ["http://news.163.com/18/0625/09/DL4SBKLP0001875O.html"]
    res_pk = pd.DataFrame({'urls': url_list})
    try:
        res_pk['paragraphs'] = res_pk.urls.apply(get_paragraphs)
        res_pk['tagging_words'] = res_pk.paragraphs.apply(get_tagging_words, args=(True,))
        res_pk['tagging_words_enrich'] = res_pk.tagging_words.apply(get_similarities, args=(m, True))
    finally:
        with open(outfile, 'wb') as f:
            pk.dump(res_pk, f)


def get_article_keywords_with_url(url):

    try:
        paragraphs = get_paragraphs(url)
        tagging_words = get_tagging_words(paragraphs, False)
        #tagging_words_enrich = get_similarities(tagging_words, m, True)
#        print(tagging_words_enrich)
        return tagging_words
    except Exception:
        logger.error(traceback.format_exc())
        return {}

if __name__ == "__main__":
    i=0
    with open('/Users/mafeipeng/Desktop/Url') as f:
        for line in f:
            i=i+1
            print(i)
            print(line)
            if ".pdf" in line:
                continue
            else:
                get_article_keywords_with_url(line)
            file.write("\n")

    #get_article_keywords_with_url("http://a.cdn.intentmedia.net/a1/exit_unit.html?publisher_user_id=9E9FB547AF4840A6ABC5B047985E8B3F&ad_unit_tag_id=orb_us_sca_flt_lst_xu_bex&exit_unit_source=flight_list_page&origination=PVG&destination=SAO&page_id=flights.results.redesign&site=ORBITZ_BEX&site_country=US&site_language=en&site_currency=USD&exit_unit_remote_polling=false&bucket=a1&privacy_policy_link=https%3A%2F%2Fwww.orbitz.com%2Fprivacy&use_site_specific_xu_js=true&site_reporting_value_01=11700_0%3A13604_0&site_reporting_value_06=page.flight-search-roundtrip.out&page_initialization_id=81e11315-d98a-4a51-9633-1abc39293da4&page_view_type=LIST&trip_type=ROUND_TRIP&flight_origin=PVG&flight_destination=SAO&show_overlay=N&travel_date_start=20170602&travel_date_end=20170602&travelers=1&adults=1&children=0&display_format_type=Desktop&show_ads=Y&show_exit_units=Y&publisher_session_id=264a16f8-0e67-4f22-82e6-5c9399d4b0b4&is_member=N&is_logged_in_user=N&product_category=flights&is_signed_up_for_promo_email=N&user_previously_searched=N&expedia_cookie_aspp=v.1%2C0%7C%7C%7C%7C%7C%7C%7C%7C%7C%7C%7C%7C%7C&publisher_user_id_hashed=943d949c49a359a61ccbef2619eb2fc2&publisher_session_id_hashed=a8a1cc48e4adc6d3757e2240ee002374&cache_buster=4583745&screen_width=1600&screen_height=770&screen_pixel_depth=24&time_zone_offset=480&site_name=ORBITZ_BEX&screen_size=full_screen&hotel_airport_code=SAO&requested_number_of_prechecks=2&parent_height=860&parent_width=1600&parent_left=0&parent_top=0&partner_exp_ids=10912_0%3A0%3A13604_0")

    #get_article_keywords_with_url("http://abcnews.go.com/Entertainment/documentary-explores-whitney-houstons-sexuality-drug/story?id=49343037")