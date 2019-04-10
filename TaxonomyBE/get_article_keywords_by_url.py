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
from enrich_article_keywords import get_similarities
from Utils.loadfile import loadfile
from Utils.loggerhandler import mylogger
import re


def check_version():
    if sys.version_info < (3, 0):
        sys.stdout.write('Please use python 3.x to run this script!\n')
        sys.exit(255)


check_version()

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
m = Word2Vec.load(m_path)

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
        tagging_words_enrich = get_similarities(tagging_words, m, True)
        print(tagging_words_enrich)
        return tagging_words, tagging_words_enrich
    except Exception:
        logger.error(traceback.format_exc())
        return {}

if __name__ == "__main__":

    get_article_keywords_with_url("http://news.163.com/18/0625/09/DL4SBKLP0001875O.html")