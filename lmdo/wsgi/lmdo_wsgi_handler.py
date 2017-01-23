import os
import sys

file_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(file_path, "./"))
sys.path.append(os.path.join(file_path, "./vendored"))


import json
import datetime
import logging
import traceback
import logging

from wsgi_apps.response.apigateway_response import ApigatewayResponse
from wsgi_apps.apps.django_app import get_django
from wsgi_apps.lmdowsgi import LmdoWSGI

# Set up logging
logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class LambdaHandler(object):
    """
    """
    
    def __init__(self):
       self._wsgi = LmdoWSGI()

    def apigateway(self, event, context):
        """Handle reqeust from api gateway"""
        apigateway_response = ApigatewayResponse()
        logger.info(event) 
        try:
            time_start = datetime.datetime.now()

            environ = self._wsgi.translate(event, context)
            response = apigateway_response.run_app(get_django(), environ)

            response_time_ms = (datetime.datetime.now() - time_start).total_seconds() * 1000
            #self._wsgi.log(environ, response, response_time=response_time_ms)

            return response
        except Exception as e:

            print(e)
            exc_info = sys.exc_info()

            # Return this unspecified exception as a 500, using template that API Gateway expects.
            content = {}
            content['statusCode'] = 500
            body = {'message': 'django error'}
            #if settings.DEBUG:  # only include traceback if debug is on.
            #    body['traceback'] = traceback.format_exception(*exc_info)  # traceback as a list for readability.
            content['body'] = json.dumps(body, sort_keys=True, indent=4).encode('utf-8')
            return content


def handler(event, context):
    return LambdaHandler().apigateway(event, context)


