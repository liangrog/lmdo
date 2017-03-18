import logging
import importlib
import imp

# Set up logging
logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)

try:
    # If django framework exists
    django_file, pathname, description = imp.find_module('django')
    import django
    django.setup()
except ImportError:
    logger.info('No Django package found (won\'t be an issue if you are not using it)')
except Exception as e:
    logger.info(e)    

def handler(event, context):
    # Only deal with schedule events
    if event['source'] == 'aws.events':
        arn_prefix, rule_name = event['resources'][0].split('/')
        prefix, module = rule_name.split('--')
        func = module.split('.')[-1]
        module = '.'.join(module.split('.')[0:-1])
        obj = importlib.import_module(module)
        return getattr(obj, func)(event, context)

    return False
