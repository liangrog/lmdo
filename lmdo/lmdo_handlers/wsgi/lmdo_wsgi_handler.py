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
       self._django = get_django()

    def apigateway(self, event, context):
        """Handle reqeust from api gateway"""
        if not event:
            return False

        apigateway_response = ApigatewayResponse()

        if self._settings.DEBUG:
            logger.info(json.dumps(event)) 

        try:
            if event.get('heater'):
                logger.info('Pinged by heater')
                return {"alive": context.function_name}

            time_start = datetime.datetime.now()
            
            environ = self._wsgi.translate(event, context)
           
            if self._settings.DEBUG:
                logger.info(environ) 

            response = apigateway_response.run_app(self._django, environ)

            if self._settings.DEBUG:
                time_end = datetime.datetime.now()
                delta = time_end - time_start
                logger.info('Django app run time {} milliseconds'.format(str(delta.total_seconds()*1000)))

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

handler_singleton = LambdaHandler()

def handler(event, context):
    return handler_singleton.apigateway(event, context)


