
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
            result['statusCode'] = from_data.status_code
            result['headers'] = {}
            for key, value in from_data.headers:
                result['headers'][key] = value

        return result


