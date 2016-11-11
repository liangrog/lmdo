"""
lmdo system wide configuration
"""

# File for all config data
config_template = 'lmdo.yml.j2'
config_file = 'lmdo.yml'

# Template file name
cf_file = 'cf.template'
swagger_file = 'apigateway.json'

# Where temporary files saved to
tmp_dir = '/tmp/lmdo/'

# Template location
cf_dir = './cloudformation/'
swagger_dir = './swagger/'

# Mandatory keys in the config file
config_mandatory_keys = [
    'Profile',
    'Environment',
    'User',
    'LambdaBucketName', 
    'Stage', 
    'Service' 
    ]
    
# Default AWS credential profile
profile = 'default'

# Files and directories excluding from packaging
exclude = {
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


