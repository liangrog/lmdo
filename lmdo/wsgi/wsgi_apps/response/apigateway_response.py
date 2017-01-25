import os
import importlib
from werkzeug.wrappers import Response

from .response_interface import ResponseInterface


class ApigatewayResponse(ResponseInterface):
    def run_app(self, app, environ):
        """Run wsgi app and return result back to Lambda"""
        response = Response.from_app(app, environ)
        return self.translate(response)

    def translate(self, from_data):
        """Translate data to apigateway"""
        result = {}
        if from_data.data:
            result['body'] = from_data.data
            result['statusCode'] = from_data._status_code
            result['headers'] = {}
            for key, value in from_data.headers:
                result['headers'][key] = value
        
        settings = importlib.import_module(os.environ["DJANGO_SETTINGS_MODULE"])
        if settings.CORS_ENABLED:
            result['headers']['Access-Control-Allow-Headers'] = 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,x-requested-with'
            result['headers']['Access-Control-Allow-Methods'] = 'DELETE,GET,OPTIONS,PUT,POST'
            result['headers']['Access-Control-Allow-Origin'] = '*'

        return result


