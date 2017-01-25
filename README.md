lmdo
=========
A simple CLI tool for developing microservices using AWS Lambda function (python2.7) and managing logistic of AWS resources


Purpose
-------

The existing open source tool sets such as [Apex](https://github.com/apex/apex) and [Serverless](https://github.com/serverless/serverless) have all sorts of limitations and too much abstractions. Understandably tools are often opinionated but flexibility should be allowed.

In our case, we want to use cloudformation and swagger tempalte to manage our AWS resource and also we want to be able to build standard Lambda function or use Django in Lambda. 

lmdo allows:
- Use cloud formation templates
- Use swagger for API Gateway
- Individually managing AWS resources
- Manage life cycles of AWS Lambda functions
- Bridge Django framework
- Tail Cloudwatch logs

Usage
-----

    lmdo init <project_name>
    lmdo bp fetch <url>
    lmdo cf (create|update|delete)
    lmdo lm (create|update|delete) [--function-name=<functionName>]
    lmdo api (create|update|delete)
    lmdo api create-stage <from_stage> <to_stage>
    lmdo api delete-stage <from_stage>
    lmdo api create-domain <domain_name> <cert_name> <cert_path> <cert_private_key_path> <cert_chain_path>
    lmdo api delete-domain <domain_name>
    lmdo api create-mapping <domain_name> <base_path> <api_name> <stage>
    lmdo api delete-mapping <domain_name> <base_path>
    lmdo s3 sync
    lmdo logs tail function <function_name> [-f | --follow] [--day=<int>] [--start-date=<datetime>] [--end-date=<datetime>]
    lmdo logs tail <log_group_name> [-f | --follow] [--day=<int>] [--start-date=<datetime>] [--end-date=<datetime>]
    lmdo deploy
    lmdo destroy
    lmdo (-h | --help)
    lmdo --version

    Options:
    -h --help                      Show this screen.
    --version                      Show version.
    --day=<int>                    Day to search e.g. 5, -10
    --start-date=<datetime>        Start date in format 1970-01-01
    --end-date=<datetime>          End date in format 1970-01-01
    -f --follow                    Follow entry
    --function-name=<functioName>  Lambda function name
    --group-name=<groupName>       Cloudwatch log group name
    
    
Installation
-----
    $ sudo pip install lmdo


Project initiation
-----
To initiate your project, run

    $ lmdo init <project_name>
    
This will create a project folder and the sample lmdo configuration file `lmdo.yml` for you.

**Note**: Apart from the init command, all other lmdo commands need to be run at the same directory of the lmdo.yml file

AWS credentials
-----
You can either use session (`Profile`) or configure AWS key and secret (`AWSKey, AWSSecret`) in lmdo.yml

If using session, you will need to create two files:

    ~/.aws/config and ~/.aws/credentials

Details pleae ref to [AWS CLI](http://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html)

Boiler plating
-----
To get a boiler plate repo from somewhere in github, run

    $ lmdo bp fetch <url>
    
The repo will then be copied from github to your current project folder without all the git folders or files

AWS Cloudformation
-----
To use cloudformation, you need to 

1. create a folder named `cloudformation` in your project folder, so it looks like:

        <your-project>/cloudformation
   The cloudformation template can be in any of `.yml`, `.json` or `.template` format as per AWS requirements. 
    
2. there has to be one master template and named `main.*` regardless you are using single template or nested stacks. 
   
   If using nested stacks, you must provide S3 bucket in your lmdo.yml file under `CloudformationBucket` as per AWS requirements.

    For single template, if no S3 bucket provided, the template will be loaded from your local. 

3. If there are parameters, all parameters with their values must be provided in the file named `params.json`. This file however won't be uploaded to S3 under all scenarios for security reasons.

4. If `StackName` is provided in lmdo.yml, it'll be used to create the stack. Otherwise lmdo will use `<user>-<stage>-<service-name>-service` to name your stack

To manage your cloudformation resource, run:

    $ lmdo cf (create|update|delete)
    
AWS Lambda
-----
You can create standard lambda function and or use a bridging lambda function provided by lmdo to connect to your django app. Lmdo allows you to create any number of lambda functions.

1. Standard Python Lambda function

   **Requirements**
   
   * The invokable lambda function files need to be placed on the top level of the project folder. 
   * The `requirements.txt` file and `vendored` folder are required under the project folder. 
   * All the pip installations will be installed in the `vendored` folder.
   
   **Writting your Lambda function**
   
   Add below lines at the beginning of your lambda function file so all your modules can be found by AWS Lambda runtime:

        import os
        import sys

        module_path = os.path.dirname(os.path.realpath(__file__))
        sys.path.append(os.path.join(module_path, "./"))
        sys.path.append(os.path.join(module_path, "./vendored"))

    **lmdo.yml configuration**
    
    To configure your lambda, enter an entry under `Lambda`:

          S3Bucket: lambda.bucket.name        # mandatory, the bucket to load your package to
          Type: default                       # Optional, other types is django
          FunctionName: superman              # mandatory, the actual function name in AWS will have the format of <user>-<stage>-<service-name>-<FunctionName>
          Handler: handler.fly                # mandatory, define the handler function
          MemorySize: 128                     # optional, default to 128
          RoleArn: rolearn                    # Either provide a role arn or assume role policy doc, the RolePolicyDocument takes preccedent
          RolePolicyDocument: path/to/policy  # Assume role Policy
          Runtime: python2.7                  # optional default to 'python2.7'
          Timeout: 180                        # optional default to 180
          VpcConfig:                          # optional, Lambda VPC configuration
              SecurityGroupIds:
                  - string
                  - string
              SubnetIds:
                  - string
                  - string
          EnvironmentVariables:              # optional, runtime environment variable
              MYSQL_HOST: localhost
              MYSQL_PASSWORD: secret
              MYSQL_USERNAME: admin
              MYSQL_DATABASE: lmdo
 
2. Django app

   **Requirements**
   
   * The `requirements.txt` file and `vendored` folder are required under the project folder. 
   * All the pip installations will be installed in the `vendored` folder.
   
   **lmdo.yml configuration**
   
   To config, add below entry in `Lambda`:
   
         S3Bucket: lambda.bucket.name        # mandatory
         Type: django                        # Other types
         DisableApiGateway: False            # Optional, if set to True, the apigateway for Django app won't be created
         ApiBasePath: /path                  # Mandatory if apigateway to be created. Base resource path for django app
         FunctionName: superman              # mandatory
         MemorySize: 128                     # optional, default to 128
         RoleArn: rolearn                    # Either provide a role arn or assume role policy doc, the RolePolicyDocument takes preccedent
         RolePolicyDocument: path/to/policy  # Assume role Policy
         Runtime: python2.7                  # optional default to 'python2.7'
         Timeout: 180                        # optional default to 180
         VpcConfig:                          # optional
             SecurityGroupIds:
                 - string
                 - string
             SubnetIds:
                 - string
         EnvironmentVariables:                       # mandatory
             DJANGO_SETTINGS_MODULE: mysite.settings # mandatory
 
 
To deploy all the functions, run

    $ lmdo lm (create|update|delete)

To only deploy one function, run
    
    $ lmdo lm (create|update|delete) --function-name=blah

AWS API Gateway
-----
1. Standard API Gateway
   Swagger template is used to create API Gateway

    **Requirements**
    
    * A folder named 'swagger' under your project folder
    * Name your swagger template as `apigateway.json`

    **lmdo.yml configuration**
    
        ApiGatewayName: Your unique Apigateway name
    
    **NOTE:** Please name your version as `$version` and your title as `$title` so that Lmdo can update it during creation using the value of `ApiGatewayName` in your lmdo.yml.

2. WSGI(Django) API
   Lmdo automatically create a API Gateway resource if you have Django Lambda function configured using proxy unless you have `DisableApiGateway` set to `True` in your Lambda function config in `lmdo.yml`. There will only be one API gateway created. Django api will be appended as part of the resource

To manage your APIGateway resource, run:

    $ lmdo api (create|update|delete)
    
You can create or delete a stage by running

    $ lmdo api create-stage <from_stage> <to_stage>
    or 
    $ lmdo api delete-stage <from_stage>

AWS S3
-----
Lmdo offers a simple command line to upload your local static asset into a S3 bucket. All you need to do is to configure `AssetS3Bucket` and `AssetDirectory` in your lmdo.yml, then run

    $ lmdo s3 sync

    
AWS Cloudwatch Logs
-----
1. You can tail any AWS cloudwatch group logs by running:

        $ lmdo logs tail <log_group_name> [-f | --follow] [--day=<int>] [--start-date=<datetime>] [--end-date=<datetime>]

    `--day` value defines how many days ago the logs need to be retrieved or you specify a start date and/or end date for the log entries using format `YYYY-MM-DD`

2. You can also tail logs of your lambda function in your project by running:

        $ lmdo logs tail function <function_name> [-f | --follow] [--day=<int>] [--start-date=<datetime>] [--end-date=<datetime>]

  The `<function_name>` is the name you configure in your lmdo.yml

One step deployment
-----
Alternatively, you can deploy and delete your entire service by running
    
    $ lmdo deloy 
        or
    $ lmdo destroy


