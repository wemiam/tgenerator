# -*- coding: utf-8 -*-
import functools
import sys
import os
import time
try:
    import cPickle as pk
except:
    try:
        import _pickle as pk
    except:
        import pickle as pk
import traceback
from Utils.loggerhandler import mylogger


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


#取关键词之间相似度
def get_similarities(words, m, verbose=False):
    res = dict()
    for i, w in enumerate(words):
        w_detail = dict()
        w_similarities = []
        for j, y in enumerate(words):
            if i != j and words[i] in m.wv.vocab and words[j] in m.wv.vocab:
                similarity = m.similarity(words[i], words[j])
                w_similarities.append([words[j], similarity])
            elif i != j and words[i].encode('utf-8') in m.wv.vocab and words[j].encode('utf-8') in m.wv.vocab:
                similarity = m.similarity(words[i].encode('utf-8'), words[j].encode('utf-8'))
                w_similarities.append([words[j], similarity])
            elif i != j:
                similarity = 'unknown'
                w_similarities.append([words[j], similarity])
        w_similarities = sorted(w_similarities, key=functools.cmp_to_key(lambda x, y: 1 if x[1] == 'unknown' else -1 if y[1] == 'unknown' else y[1] - x[1]))
        w_detail['similarities'] = w_similarities
        res[w] = w_detail

    # log result
    if verbose:
        for x in res.keys():
            logger.debug(x)
            if 'similarities' in res[x]:
                for y in res[x]['similarities']:
                    logger.debug('{} {} {}'.format(x, y[0], y[1]))
    return res





def main(verbose=False):
    df = pk.load(open(infile, 'rb'), encoding='latin1')
    try:
        df['tagging_words_enrich'] = df.tagging_words_enrich.apply(get_entities, args=(True,))
    finally:
        with open(outfile, 'wb') as f:
            pk.dump(df, f)
    if verbose:
        for i in df.index:
            logger.info('-' * 50 + ' {} '.format(i) + '-' * 50)
            a = df.loc[i, 'tagging_words_enrich']
            for k in a:
                logger.info('*' * 25 + ' {} '.format(k) + '*' * 25)
                entity = a.get(k).get('entity')
                if entity == 'UNKNOWN':
                    continue
                logger.info('{} {}'.format(k, entity))
                similarities = a.get(k).get('similarities')
                for s in similarities:
                    logger.info('{} {}'.format(s[0], s[1]))


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.stderr.write('\tneed parameters:\tinfile, outfile\n')
        sys.exit(255)

    infile = os.path.abspath(sys.argv[1])
    outfile = os.path.abspath(sys.argv[2])

    # check parameter
    if not os.path.exists(infile):
        sys.stderr.write('$infile does not exist: {}\n'.format(infile))
        sys.exit(254)

    outpath = os.path.dirname(outfile)
    __makesuredirexist__(outpath)

    # prepare
    logger.info('{}'.format(str(sys.argv)))

    # define constants

    # process
    start_time = time.time()
    logger.info('start')
    try:
        main(True)
    except Exception:
        logger.error("Unexpected error: \n%s", traceback.format_exc())
    finally:
        end_time = time.time()
        logger.info('end')
        logger.info('elapsed {} seconds'.format(end_time - start_time))
