import os
import sys

file_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(file_path, "./"))
sys.path.append(os.path.join(file_path, "./vendored"))


import json
import importlib
import datetime
import logging

from wsgi_apps.response.apigateway_response import ApigatewayResponse
from wsgi_apps.apps.django_app import get_django
from wsgi_apps.lmdowsgi import LmdoWSGI

# Set up logging
logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class LambdaHandler(object):
    """Handler class"""
    
    def __init__(self):
       self._wsgi = LmdoWSGI()
       self._settings = importlib.import_module(os.environ["DJANGO_SETTINGS_MODULE"])

    def apigateway(self, event, context):
        """Handle reqeust from api gateway"""
        apigateway_response = ApigatewayResponse()

        if self._settings.DEBUG:
            logger.info(event) 

        try:
            time_start = datetime.datetime.now()

            environ = self._wsgi.translate(event, context)
            response = apigateway_response.run_app(get_django(), environ)

            return response
        except Exception as e:
            exc_info = sys.exc_info()

            # Return this unspecified exception as a 500, using template that API Gateway expects.
            content = {}
            content['statusCode'] = 500
            body = {'message': 'application error'}
            content['body'] = json.dumps(body, sort_keys=True, indent=4).encode('utf-8')
            return content


def handler(event, context):
    return LambdaHandler().apigateway(event, context)


