"""
lmdo system configuration
"""

# Where temporary files saved to
TMP_DIR = '/tmp/lmdo/'

# File for lmdo project config data
PROJECT_CONFIG_TEMPLATE = 'lmdo.yml.j2'
PROJECT_CONFIG_FILE = 'lmdo.yml'

# PIP
PIP_VENDOR_FOLDER = 'vendored'
PIP_REQUIREMENTS_FILE = 'requirements.txt'

# Cloudformations
CLOUDFORMATION_DIRECTORY = 'cloudformation'
CLOUDFORMATION_TEMPLATE_ALLOWED_POSTFIX = ['json', 'template', '.yml']
CLOUDFORMATION_TEMPLATE = 'main'
CLOUDFORMATION_PARAMETER_FILE = 'params.json'

# Lambda
LAMBDA_MEMORY_SIZE = 128
LAMBDA_RUNTIME= 'python2.7'
LAMBDA_TIMEOUT = 180

# Files and directories excluding from packaging
LAMBDA_EXCLUDE= {
    'dir': [
        'tests',
        '*boto*',
        '*.git*',
        '.cache',
        'cloudformation',
        'swagger',
    ],
    'file': [
        'lmdo.yml',
        '*.pyc',
        '.gitignore',
        '.coverage',
        '.travis.yml',
        'requirement.txt',
    ]
}

# Apigateway
SWAGGER_DIR = 'swagger'
SWAGGER_FILE = 'apigateway.json'

# S3
S3_UPLOAD_EXCLUDE = {
    'dir': [
        '*.git*',
        '.gitignore',
        '*.md'
    ],
    'file': [
        '.DS_Store'
    ]
}

# Mandatory keys in the config file
CONFIG_MANDATORY_KEYS= [
    'User', 
    'Stage', 
    'Service',
    'Profile'
]
    


"""
lmdo.yml:

User: user
Stage: dev
Service: lmdo
Profile: default

CloudformationBucket: cloudformation.bucket.name

StaticS3Bucket: static.bucket.name
StaticDirectory: ./build

Lambda:
    - EnvironmentVariables:
          MYSQL_HOST: localhost
          MYSQL_PASSWORD: secret
          MYSQL_USERNAME: admin
          MYSQL_DATABASE: lmdo
      S3Bucket: lambda.bucket.name
      FunctionName: superman
      Handler: handler.fly
      MemorySize: 128
      Role:
      RolePolicyDocument:
      Runtime:
      Timeout:
      VpcConfig: 
          SecurityGroupIds:
          SubnetIds:
       
"""


