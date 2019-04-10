# python3
import os
import traceback
from json import dumps

from Utils.loggerhandler import mylogger
from get_article_keywords_by_url import get_article_keywords_with_url
from taxonomy import get_taxonomy
from flask import Flask , Blueprint , render_template, request, Response

__author__ = 'wemiam'


# prepare logger
jobname = os.path.splitext(os.path.basename(__file__))[0]
rootdir = os.path.dirname(os.path.abspath(__file__))
log_path = rootdir + os.path.sep + 'log'
log_file = log_path + os.path.sep + jobname + '.log'
if not os.path.exists(log_path):
    os.makedirs(log_path, 0o775)
logger = mylogger(jobname, log_file)


app = Flask(__name__, static_url_path='/static/')
ai_web_api = Blueprint('ai_web_api', __name__)


@ai_web_api.before_request
def before_request():
    logger.debug('request %s %s %s %s %s', request.remote_addr, request.method, request.scheme, request.full_path,
                 request.json)


@ai_web_api.route('/', defaults={'path': ''})
@ai_web_api.route('/<path:path>')
def index(path):
    return render_template('index.html')


@ai_web_api.route('/analyseUrl', methods=['POST'])
def analyse_url():
    try:
        content = request.data
        data = eval(content)

        url = data['url']
        keywords, taxonomy_input = get_article_keywords_with_url(url)
        #keywords = []
        #for key in taxonomy_input.keys():
        #    keywords.append(key)

        taxonomy = get_taxonomy(keywords, taxonomy_input)

        res = {
            'keywords': keywords,
            'taxonomy': taxonomy
        }

        return Response(dumps({"result": res, "success": True}), mimetype="application/json;charset=utf8")
    except Exception:
        logger.error(traceback.format_exc())
        error_info = traceback.format_exc()
        return Response(dumps({"result": error_info, "success": False}), mimetype="application/json;charset=utf8")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)