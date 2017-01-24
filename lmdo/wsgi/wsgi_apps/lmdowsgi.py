import logging
import json
from urllib import urlencode
from requestlogger import ApacheFormatter
from StringIO import StringIO

from werkzeug import urls


class LmdoWSGI(object):
    """Processing lambda event object to wsgi"""

    def __init__(self, event=None, context=None):
        if event:
            self._environ = self.translate(event, context)

    @property
    def environ(self):
        return self._environ

    def translate(self, event, context=None):
        """Translating lambda event to wsgi dict"""
        environ = {}

        # Standard wsgi
        environ['REQUEST_METHOD'] = event['httpMethod']
        
        x_forwarded_for = event['headers'].get('X-Forwarded-For', '')
        if ',' in x_forwarded_for:
            environ['REMOTE_ADDR'] = x_forwarded_for.split(', ')[0]
        else:
            environ['REMOTE_ADDR'] = '127.0.0.1'

        environ['REMOTE_PORT'] = event['headers'].get('X-Forwarded-Port', '')

        environ['PATH_INFO'] = urls.url_unquote('/' + str(event['path'].split('/', 2).pop())) 
        
        if event.get('queryStringParameters'):
            environ['QUERY_STRING'] = urlencode(event.get('queryStringParameters'))
        else:
            environ['QUERY_STRING'] = ''

        environ['SCRIPT_NAME'] = ''
        environ['SERVER_NAME'] = 'lmdo'
        environ['SERVER_PORT'] = '80'
        environ['SERVER_PROTOCOL'] = str('HTTP/1.1')

        if event.get('body'):
            environ['CONTENT_LENGTH'] = str(len(event.get('body')))
            environ['wsgi.input'] = StringIO(event.get('body'))
        else:
            environ['CONTENT_LENGTH'] = '0'
            environ['wsgi.input'] = StringIO('')

        environ['wsgi.version'] = (1, 0)
        environ['wsgi.url_scheme'] = 'https'
        environ['wsgi.errors'] = ''
        environ['wsgi.multiprocess'] = False
        environ['wsgi.multithread'] = False
        environ['wsgi.run_once'] = False

        if event['headers'].get('Content-Type'):
            environ['CONTENT_TYPE'] = event['headers'].get('Content-Type')


        for header in event['headers']:
            wsgi_name = "HTTP_" + str(header.upper().replace('-', '_'))
            environ[wsgi_name] = str(event['headers'].get(header))

        # API Gateway params
        environ['APIGATEWAY_HEADERS'] = event['headers']
        environ['APIGATEWAY_STAGE_VAR'] = event['stageVariables']
        environ['APIGATEWAY_BASE64'] = event['isBase64Encoded']
        environ['APIGATEWAY_PATH_PARAMS'] = event['pathParameters']
        environ['APIGATEWAY_REQUEST_CONTEXT'] = event['requestContext']
        environ['APIGATEWAY_PATH'] = event['path']
        environ['APIGATEWAY_RESOURCE'] = event['resource']
        environ['APIGATEWAY_QUERY_STRING_PARAMS'] = event['queryStringParameters']
        environ['APIGATEWAY_BODY'] = event['body']
        environ['APIGATEWAY_HTTP_METHOD'] = event['httpMethod']

        # Lambda context object
        environ['LAMBDA_CONTEXT'] = context

        # Local copy
        self._environ = environ

        return environ

    @classmethod
    def log(cls, environ, response, response_time=None):
        """
        Given the WSGI environ and the response,
        log this event in Common Log Format.

        """
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)

        if response_time:
            formatter = ApacheFormatter(with_response_time=True)
            try:
                log_entry = formatter(response.status_code, environ,
                                      len(response.content), rt_us=response_time)
            except TypeError:
                # Upstream introduced a very annoying breaking change on the rt_ms/rt_us kwarg.
                log_entry = formatter(response.status_code, environ,
                                      len(response.content), rt_ms=response_time)
        else:
            formatter = ApacheFormatter(with_response_time=False)
            log_entry = formatter(response.status_code, environ,
                                  len(response.content))

        logger.info(log_entry)

        return log_entry

