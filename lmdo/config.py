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

# Template file name
swagger_file = 'apigateway.json'

# Template location
cf_dir = './cloudformation/'
swagger_dir = './swagger/'

# Mandatory keys in the config file
config_mandatory_keys = [
    'Environment',
    'LambdaBucketName', 
    'Stage', 
    'Service' 
]
    


"""
User
Stage
Service
StackName
CloudformationBucket
                "EnvironmentVariables": {
                        "MYSQL_HOST": {"Ref": "MysqlHost"},
                        "MYSQL_PASSWORD": {"Ref": "MysqlPassword"},
                        "MYSQL_USERNAME": {"Ref": "MysqlUsername"},
                        "MYSQL_DATABASE": {"Ref": "MysqlDatabase"},
                        "REGION": {"Ref": "AWS::Region"}
                },
                "Bucket"
                "FunctionName"
                "Handler"
                "MemorySize" 128
                "Role":
                "RolePolicyDocument":
                "Runtime"
                "Timeout" 180
                "VpcConfig": {
                    "SecurityGroupIds"
                    "SubnetIds"
                }
            }
"""
