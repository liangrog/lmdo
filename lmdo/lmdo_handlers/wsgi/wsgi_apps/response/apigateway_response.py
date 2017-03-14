import os
import importlib
from werkzeug.wrappers import Response

from .response_interface import ResponseInterface


class ApigatewayResponse(ResponseInterface):
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
 
        # Make sure we set stage before the actual Location URL
        # So it works with API gateway stage URL if the redirection
        # URL is relative
        if result['statusCode'] >= 300 and result['statusCode'] < 400 \
            and result['headers'].get('Location') \
            and not result['headers'].get('Location').startswith('http')
            and environ['APIGATEWAY_REQUEST_CONTEXT'].get('stage'):

            stage = environ['APIGATEWAY_REQUEST_CONTEXT']['stage']
            result['headers']['Location'] = '/{}{}'.format(stage, result['headers']['Location'])
 
        settings = importlib.import_module(os.environ["DJANGO_SETTINGS_MODULE"])
        if settings.CORS_ENABLED:
            result['headers']['Access-Control-Allow-Headers'] = 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,x-requested-with'
            result['headers']['Access-Control-Allow-Methods'] = 'DELETE,GET,OPTIONS,PUT,POST'
            result['headers']['Access-Control-Allow-Origin'] = '*'
        
        return result


