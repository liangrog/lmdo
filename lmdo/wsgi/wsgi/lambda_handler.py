import datetime
import logging
import traceback

import os
import sys
import logging

sys.path.append('/var/task')
file_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(file_path, "./"))
sys.path.append(os.path.join(file_path, "./vendored"))


from .response.apigateway_response import ApigatewayResponse
from .apps.django import get_django


# Set up logging
logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class LambdaHandler(object):
    """
    """
    
    def __init__(self):
       self._wsgi = WSGI()

    def apigateway(self, event, context):
        """Handle reqeust from api gateway"""
        apigateway_response = ApigatewayResponse()
        
        try:
            time_start = datetime.datetime.now()

            environ = self._wsgi.translate(event)
            response = apigateway_response.run_app(self.get_app, environ)

            response_time_ms = (datetime.datetime.now() - time_start).total_seconds() * 1000
            common_log(environ, response, response_time=response_time_ms)

            return response
        except Exception as e:

            print(e)
            exc_info = sys.exc_info()

            # Return this unspecified exception as a 500, using template that API Gateway expects.
            content = collections.OrderedDict()
            content['statusCode'] = 500
            body = {'message': 'django error'}
            #if settings.DEBUG:  # only include traceback if debug is on.
            #    body['traceback'] = traceback.format_exception(*exc_info)  # traceback as a list for readability.
            content['body'] = json.dumps(body, sort_keys=True, indent=4).encode('utf-8')
            return content


def handler(event, context):  # pragma: no cover
    return LambdaHandler().apigateway(event, context)

