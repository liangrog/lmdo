import os
import importlib
import logging
import json
import base64

from werkzeug.wrappers import Response

from .response_interface import ResponseInterface

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class ApigatewayResponse(ResponseInterface):
    """Prepare response for apigateway"""
    def run_app(self, app, environ):
        """Run wsgi app and return result back to Lambda"""
        response = Response.from_app(app, environ)
        return self.translate(response, environ)

    def translate(self, from_data, environ):
        """Translate data to apigateway"""
        result = {}
        result['body'] = from_data.data or ''
        result['statusCode'] = from_data._status_code

        result['headers'] = {}
        for key, value in from_data.headers.iteritems():
            result['headers'][key] = value
 
        settings = importlib.import_module(os.environ["DJANGO_SETTINGS_MODULE"])
        if settings.CORS_ENABLED:
            result['headers']['Access-Control-Allow-Headers'] = 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,x-requested-with'
            result['headers']['Access-Control-Allow-Methods'] = 'DELETE,GET,OPTIONS,PUT,POST'
            result['headers']['Access-Control-Allow-Origin'] = '*'

        # Binary support
        default_mime_type = 'json'
        if not from_data.mimetype.startswith("text/") \
            and default_mime_type not in from_data.mimetype:
            result['body'] = base64.b64encode(result['body'])
            result["isBase64Encoded"] = "true"

        self.response_log(from_data, environ)

        return result

    def response_log(self, response, environ):
        """Log response for assessment"""
        log_str = '{} {} {} {}'.format(
            environ['APIGATEWAY_REQUEST_CONTEXT']['httpMethod'], 
            environ['PATH_INFO'],
            str(response._status_code),
            environ['APIGATEWAY_REQUEST_CONTEXT']['identity']['userAgent'])

        log_dict = {
            "httpMethod": environ['APIGATEWAY_REQUEST_CONTEXT']['httpMethod'],
            "path": environ['PATH_INFO'],
            "userAgent": environ['APIGATEWAY_REQUEST_CONTEXT']['identity']['userAgent'],
            "stage": environ['APIGATEWAY_REQUEST_CONTEXT']['stage'],
            "responseStatusCode": response._status_code,
            "responseDefaultMimeType": response.default_mimetype,
            "responseMimeType": response.mimetype,
            "responseContentEncoding": response.content_encoding
        }

        logger.info(log_str)
        logger.info(json.dumps(log_dict))


