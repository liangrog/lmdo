import logging
import importlib
import boto3
import json

# Set up logging
logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    logger.info(event)
    if event['source'] == 'aws.events':
        arn_prefix, rule_name = event['resources'][0].split('/')
        prefix, function_name = rule_name.split('--')
        payload = {'heater': True}
        client = boto3.client('lambda')
        response = client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            LogType='None',
            Payload=json.dumps(payload))

        logger.info(function_name)
        return True

    return False
