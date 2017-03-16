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
        payload = {}
        client = boto3.client('lambda')
        client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            LogType='None',
            ClientContext='lmdo_heater',
            Payload=json.dumps(payload))

    return False
