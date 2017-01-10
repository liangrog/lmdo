"""
lmdo system configuration
"""

# Where temporary files saved to
tmp_dir = '/tmp/lmdo/'

# File for lmdo project config data
project_config_template = 'lmdo.yml.j2'
project_config_file = 'lmdo.yml'

# PIP
pip_vendor_folder = 'vendored'
pip_requirements_file = 'requirements.txt'

# Cloudformations
cloudformation_directory = 'cloudformation'
cloudformation_template_allowed_postfix = ['json', 'template']
cloudformation_template = 'main'
cloudformation_paramemter_file = 'params.json'

# Lambda
lambda_memory_size = 128
lambda_runtime = 'python2.7'
lambda_timeout = 180

# Files and directories excluding from packaging
lambda_exclude = {
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
swagger_dir = 'swagger'
swagger_file = 'apigateway.json'

# S3
s3_upload_exclude = {
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
config_mandatory_keys = [
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


