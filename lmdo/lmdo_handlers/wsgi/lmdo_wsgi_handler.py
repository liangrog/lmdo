import os
import sys
import json
import importlib
import datetime
import logging
import traceback

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
        if not event:
            return False

        apigateway_response = ApigatewayResponse()

        if self._settings.DEBUG:
            logger.info(event) 

        try:
            time_start = datetime.datetime.now()

            environ = self._wsgi.translate(event, context)

            if self._settings.DEBUG:
                logger.info(environ) 

            response = apigateway_response.run_app(get_django(), environ)

            return response
        except Exception as e:
            # Return this unspecified exception as a 500, using template that API Gateway expects.
            content = {}
            content['statusCode'] = 500
            body = {'message': 'application error'}
            
            if self._settings.DEBUG:
                body['traceback'] = traceback.format_exc()

            content['body'] = json.dumps(body, sort_keys=True, indent=4).encode('utf-8')
            return content


def handler(event, context):
    return LambdaHandler().apigateway(event, context)


