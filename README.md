lmdo
====
A CD/CI tool for developing micro-services components using AWS Lambda function (python2.7) and managing other AWS resources.

Inspirations
------------
[Apex](https://github.com/apex/apex),  [Serverless](https://github.com/serverless/serverless),
[Zappa](https://github.com/Miserlou/Zappa),
[sceptre](https://github.com/cloudreach/sceptre)

Why
---
Most of the open-source apps are very much opinionated and the model they employ doesn't always fit for the actual individual use case. In fact, there aren't a lot of flexibility provided. In addition, abstraction makes it hard to diagnose issues.

The tool I have in mind should allow raw inputs, be atomic, has important functionalities like the others and easy to use to a certain degree (You need to know what you are doing. E.g. I don't expect you to use it for creating stack if you don't know how to write a raw CloudFormation). Hence born lmdo.   

Features
--------
- Initialize project via Github boiler plate
- Use of CloudFormation templates in either json or yaml format
- Use of CloudFormation paramter files in either json or yaml format
- Manage one or more CloudFormation stacks
- Use of swagger template for API Gateway
- Manage API Gateway resources like deployments and stages
- Automatically generate API Gateway for Lambda functions
- Manage life cycles of AWS Lambda functions
- Offer two type of managed Lambda functions: Django wsgi wrapper and CloudWatch Event scheduler dispatcher
- Maintain Lambda function heart beat
- CloudWatch log output on CL
- Upload any files to S3 bucket

Contents:
---------
1. [Installation](#installation)
2. [Project initiation](#project-initiation)
3. [Basic configuration](#basic-configuration)
4. [One step deployment](#one-step-deployment)
5. [CloudFormation](#cloudformation)
4. [Lambda function](#lambda-function)
5. [API Gateway](#api-gateway)
6. [CloudWatch events](#cloudwatch-events)
7. [CloudWatch logs](#cloudwatch-logs)
8. [S3 Upload](#s3-upload)
8. [Environment Variables](#environment-variables)

Installation
------------
Installing via pypi:

    $ sudo pip install lmdo

Installing via code (Recommended, as lmdo is under active development at the moment):

    $ git pull https://github.com/MerlinTechnology/lmdo.git
    $ cd lmdo
    $ sudo pip install -U ./

**Note**: All lmdo commands need to be run at the same directory of the `lmdo.yaml` file

Project Initiation
------------------
To initiate your project, run:

    $ lmdo init <project_name>

This will create you named project folder and the sample lmdo configuration file `lmdo.yaml`.

If you already have an existing project, you can run:

    $ lmdo init config

The configuration file `lmdo.yaml` will be copied to your current directory. If there is already one, the new configuration file will be renamed to `lmdo.yaml.copy`

To start a project by using a github boiler plate, run:

    $ lmdo bp fetch <url>

The repo will then be copied from github to your current project folder without all the git folders or files


Basic Configuration
-------------------
1. AWS credentials

    You can either use session (`Profile`) or configure AWS key and secret (`Region, AWSKey, AWSSecret`) in `lmdo.yaml`

    When using session, you will need to create two files:

        ~/.aws/config and ~/.aws/credentials

    Details please ref to [AWS CLI](http://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html)

    **Note**: If explicitly using config options `Region, AWSKey, AWSSecret`, it's recommended to define them in the environment. Using syntax like `$env|YOUR_ENV_VAR` lmdo will replace them with the actual environment value.

2. Other mandatory configuration Options

    `Service`: The name of your service/project

    `User`: The user that deploys the service/project

    `Stage`: The deployment stage

To user a different configuration file (must be in yaml format), you can use command line option `--config`, for example:
  
    $ lmdo deploy --config=custom-config-file.yaml


One Step Deployment
-------------------
To deploy your entire service, run:

    $ lmdo deploy

To delete, run:

    $ lmdo destroy


CloudFormation
--------------
### Available reserved utility variables (`WARNING`, see Note)
They will be replaced with correct value during deployment

`$env|ENV_VAR_NAME`: Environment variables, can be used both in parameters and templates.

`$template|[relative/path/from/repo/to/template/]template-file-name`: Nested stack template to be used to construct proper S3 bucket url for stack resource `TemplateURL`, mostly used in templates.

`$stack|stack-name::output-key`: The value of an existing stack's output based on key name. Can be used both in parameters and templates.

**Note**: 

- the stack referring to must exist before deployment. 
- Recommand to avoid use those variable in the template so to keep the template complying to AWS. Instead, use those variables in the parameter file to pass in as parameters

### Configuration examples:

1. Single CloudFormation template without parameters

    ```    
    CloudFormation:
        Stacks:
            - Name: your-stack-name
              TemplatePath: relative/path/to/template            
    ```        

2. Single CloudFormation template with parameters. You can either provide a single file or a directory that contains all the parameter files. If a directory is provided, lmdo will combine all files into one during deployment.

    ```
    CloudFormation:
        Stacks:
            - Name: your-stack-name
              TemplatePath: relative/path/to/template  
              ParamsPath: relative/path/to/params/file/or/directory
    ```

3. CloudFormation using S3 bucket

    ```
    CloudFormation:
        S3Bucket: your.bucket.url
        Stacks:
            - Name: your-stack-name
              TemplatePath: relative/path/to/template  
              ParamsPath: relative/path/to/params/file/or/directory
    ```  

4. Single CloudFormation template with nested stacks

    ```
    CloudFormation:
        S3Bucket: your.bucket.url
        TemplateRepoPath: relative/path/to/nested/stack/template/directory
        Stacks:
            - Name: your-stack-name
              TemplatePath: relative/path/to/template  
              ParamsPath: relative/path/to/params/file/or/directory
    ```       

    **Note**:

    a. You must provide `S3Bucket` for nested stacks as it'll be used for uploading all the templates to.

    b. All nested stack templates must reside in `TemplateRepoPath`. If not given, lmdo will look for nested stack template (see point **c** below) from the project folder by default.

    c. Using syntax like `TemplateURL: $template|[relative/path/from/repo/to/template/]your-nested-stack-template-file-name` in your master template stack resource, lmdo will replace the syntax to appropriate S3 url.
    
    d. You can use `DisablePrefix` option to create stack with exact name you give

5. Multiple CloudFormation Stacks

    ```
    CloudFormation:
        S3Bucket: your.bucket.url
        TemplateRepoPath: relative/path/to/nested/stack/template/directory
        Stacks:
            - Name: your-stack-name-1
              TemplatePath: relative/path/to/template-1  
              ParamsPath: relative/path/to/params/file-1/or/directory-1
            - Name: your-stack-name-2
              TemplatePath: relative/path/to/template-2  
              ParamsPath: relative/path/to/params/file-2/or/directory-2            
    ```

### Parameter file
Parameter file can be in either `.json` or `.yaml` format.

For json file, you can use two types of syntax:

1. Standard AWS stack parameter format

    ```
    [
        {
            "ParameterKey": "your-parameter-key-1",
            "ParameterValue": "your-parameter-value-1"
        },
        {
            "ParameterKey": "your-parameter-key-2",
            "ParameterValue": "your-parameter-value-2"
        }            
    ]
    ```

2. lmdo json format

    ```
    {
        "your-parameter-key-1": "your-parameter-value-1",
        "your-parameter-key-2": "your-parameter-value-2"
    }
    ```

3. For yaml file, the format as follow:
    
    ```
    your-parameter-key-1: your-parameter-value-1
    your-parameter-key-2: your-parameter-value-2
    ```

4. Available reserved utility variables

    They will be replaced with correct value during deployment

    `$env|ENV_VAR_NAME`: Environment variables, can be used both in parameters and templates.

    `$stack|stack-name::output-key`: The value of an existing stack's output based on key name. Can be used both in parameters and templates.
    
    `$template|[relative/path/from/repo/to/template/]template-file-name`: Nested stack template to be used to construct proper S3 bucket url for stack resource   `TemplateURL`, mostly used in templates.

    **Note**: 
  
    The stack referring to must exist before deployment.
  
    For `CommaDelimitedList` type, you can do `"$env|ENV_VAR_NAME1, $env|ENV_VAR_NAME2"`. Same to `$stack|*`.
   
### Commands

To create your CloudFormation, run:

    $ lmdo cf create

To update or delete, run the similar command using `update` or `delete` keyword

To use change-set instead of directly update stack, use `-c` or `--change_set` option:

    $ lmdo cf create -c

Stack event will be output by default, if you want to hide it,  use `-he` or `--hide-event` option:

    $ lmdo cf create -he

For only change one specific stack, use option `--stack=`


Lambda Function
---------------
lmdo facilitates packaging, uploading and managing your lambda function. Out of box, it also provides support for two types of lambda function wrapper: wsgi and event dispatcher apart from the standard Lambda function.

### Basic configuration structure


    VirtualEnv: False
    Lambda:
        - function-1 configuration
        - function-2 configuration
        ...

**Note**:
- If you are using virtualenv, please set `VirtualEnv` to `True`
- The actual deployed function name created by lmdo will be using `<user>-<stage>-<service-name>-<FunctionName>`

### Optional configurations and their default values available for all function types

`Type`: default `default`. Other availabe types are `wsgi`, `cron_dispatcher` and `go`

`MemorySize`: default `128`

`Runtime`: default `python2.7` (Note: lmdo only support python at the moment)

`Timeout`: default `180`

`HeatUp`: default `False`. Provide CPR for lambda function to keep container alive. Only avaiable for `wsgi` and `default` functions.

`HeatRate`: default `rate(4 minutes)` before container becomes inactive. Only avaiable for `wsgi` and `default` functions.

VPC configuration:

    VpcConfig:                          
        SecurityGroupIds:
            - security-group-id-1
            - security-group-id-2
        SubnetIds:
            - subnet-id-1
            - subnet-id-2

Runtime environment variables

    EnvironmentVariables:          
        MYSQL_HOST: host-url
        MYSQL_PASSWORD: password
        MYSQL_USERNAME: username
        MYSQL_DATABASE: dbname

Role and policies:

    RoleArn: your-role-arn

or

    RolePolicy:                         
        AssumeRoles:                    
            - sns.amazonaws.com         
        PolicyDocument: file/path/to/your/policy
        ManagedPolicyArns:             
            - your-managed-policy-arn      

**Note**:
- `$region` and `$accountId` are available to use in your `PolicyDocument` so you don't need to hard-code them
- Only one of `RoleArn` and `RolePolicy` required.
- If both provided, `RolePolicy` takes over.
- If none provided, lmdo will create a default role with default policy
- the default role will assume role of apigateway, lambda, events, ec2.
- the default policy will allow `lambda:InvokeFunction`, `lambda:AddPermission`, `lambda:RemovePermission` on the lambda function, `log:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents`, `ec2:DescribeNetworkInterfaces`, `ec2:CreateNetworkInterface` and `ec2:DeleteNetworkInterface` actions    
- Only extra assume roles and policies need to be configured other than the default

### Examples
1. Standard lambda function

    Requirements:

    The invokable lambda function files need to be placed on the top level of the project folder.

    Put all your dependent packages in `requirements.txt`

    Configuration:

    ```
    Lambda:
        - S3Bucket: lambda.bucket.name
          FunctionName: your-function-name
          Handler: handler.fly                
    ```

    For Standar lambda function, you can also setup event source such as S3 and SNS. When defined event ocurrs from the source, lambda function will be triggered.
    
    The configuration of event source for lambda is as below:

    ```
    Lambda:
      - S3Bucket: lambda.bucket.name
        FunctionName: your-function-name
        Handler: handler.fly                
        EventSource:
          - Type: s3
            BucketName: [name of the source bucket]
            # Optional, lmdo default to "s3:ObjectCreated:*", "s3:ObjectRemoved:*" 
            Events:
              - "s3:ObjectCreated:Put"
            # Optional
            FilterRules:
              - Name: 'prefix'|'suffix'
                Value: string
            # Optional default to False
            Delete: False
          - Type: sns
            Topic: [name of the SNS topic]
            # Optional default to False
            Delete: False
    ```

    NOTE: `Delete` will need it if you want your function to unsubscribe without deleting the lambda function, if you don't specify, it defaults to `False`

2. Django wsgi lambda function

    It wraps up Django and bridge between API gateway and your Django

    Requirements:

    Put all your dependent packages in `requirements.txt`

    Optional configuration:

    `CognitoUserPoolId`: It will set the API gateway authentication if provided. You can only have one per `ApiBasePath`

    Configuration:

    ```
    Lambda:
        - S3Bucket: lambda.bucket.name       
          Type: wsgi                       
          DisableApiGateway: False            
          ApiBasePath: /path                  
          FunctionName: your-function-name         
          EnvironmentVariables:              
              DJANGO_SETTINGS_MODULE: mysite.settings
    ```

    **Note**:

    By default, `DisableApiGateway` is set to `False`. You must set your `ApiBasePath` when it's `False`

    `DJANGO_SETTINGS_MODULE` environment variable is a must for it to work

3. Cron dispatcher

    Cron dispatcher function allows you to create multiple event schedulers on different functions via a single dispatcher.
    **Note**: lmdo will construct rule name based on `<user>-<stage>-<service-name>-<FunctionName>--<handler>`. CloudWatch events rule name can only be within 64 characters, so mind your names.

    Configuration:

    ```
    Lambda:
        - S3Bucket: lambda.bucket.name      
          Type: cron_dispatcher                     
          FunctionName: your-dispatcher-name            
          RuleHandlers:
              - Handler: your.module.handler
                Rate: your cron string e.g. Rate(1 minutes)
    ```

3. Go function

    Configuration (mostly the same as standard lambda function except below):

    ```
    Lambda:
        - ...   
          Type: go
          ExecutableName: go-exe-name   # go build package name
          EnvironmentVariables:                     
            DEBUG: true|false           # turn on/off logging           
    ```

### Available reserved utility variables (apart from `$env|name`)

They will be replaced with correct value during deployment

`$stack|stack-name::output-key`: The value of an existing stack's output based on key name. Can be used both in parameters and templates.

**Note**: 
  
The stack referring to MUST exist before deployment.
  
For `CommaDelimitedList` type, you can do `"$stack|stack-name::key1, $stack|stack-name::key2"`.

### Commands

To create all functions, run (update/delete similar):

    $ lmdo lm create

Options:
`--function-name`: Only action on a particular function

To package the function only:

    $ lmdo package --function-name=your-function-name
 
API Gateway
---------------
Swagger template is used to create API Gateway

### Requirments

* A folder named 'swagger' under your project folder
* Name your swagger template as `apigateway.json`

### Configuration

    ApiGatewayName: Your unique Apigateway name

Optionally, you can use `ApiVarMapToFile` to map your custom key to a file for replacement

    ApiVarMapToFile:                   
        $mappingKey: file/path/name               

You can also use `ApiVarMapToVar` to map any string values to your defined key. For this mapping, you can also use `$stack`, `$lmdo-lambda-arn` and `$lmdo-lambda-role` utitlity variable for the value.

`$lmdo-lambda-arn` will return the actual lambda function ARN from the function created by lmdo

`$lmdo-lambda-role` will return the role ARN for APIGateway corresponding to the lambda function created by lmdo

    ApiVarMapToVar:
        $mappingKey1: value
        $mappingKey2: $stack|stack-name::key1
        $mappingKey3: $lmdo-lambda-arn|lmdo-lambda-name
        $mappingKey4: $lmdo-lambda-role|lmdo-lambda-name
        $mappingKey5: $evn|environment_var_name


**NOTE:** Please name your version as `$version` and your title as `$title` so that Lmdo can update it during creation using the value of `ApiGatewayName` in your lmdo.yaml

### Commands

To manage your APIGateway resource, run(update/delete similar):

    $ lmdo api create

You can create or delete a stage by running:

    $ lmdo api create-stage <from_stage> <to_stage>

or

    $ lmdo api delete-stage <from_stage>

CloudWatch events
-----------------

### Configuration

    CloudWatchEvent:
        - Name: rule_name                          
          ScheduleExpression: [schedule-expression]  
          EventPatternFile: [path/to/pattern/file] 
          Targets:                                  
              - Type: default                        
                Arn: aws-resource-arn
              - Type: local                          
                FunctionName: local-function-name
                
`[schedule-expression]`: http://docs.aws.amazon.com/AmazonCloudWatch/latest/events/ScheduledEvents.html
`[path/to/pattern/file]`: http://docs.aws.amazon.com/AmazonCloudWatch/latest/events/CloudWatchEventsandEventPatterns.html

Options:

`Description`: description of your rule

`DisablePrefix`: default to `False`. If `True`, lmdo will use your rule name instead of using `<user>-<stage>-<service-name>-<rule_name>`

`RoleArn`: default lmdo will create lambda invokable role

**Note**

When target type is `local`, lmdo will replace it with your function ARN


CloudWatch Logs
-------------------

### Commands

You can tail any AWS cloudwatch group logs by running:

    $ lmdo logs tail your_log_group_name

`--day`: defines how many days ago the logs need to be retrieved

`--start-date` or `--end-date`: specify a start date and/or end date for the log entries using format `YYYY-MM-DD`

You can also tail logs of your lambda function in your project by running:

    $ lmdo logs tail function your-function-name

`your-function-name` is the function name you configure in your lmdo.yaml

S3 Upload
------

lmdo offers a simple command line to upload your local static asset into a S3 bucket.

### Configuration

    AssetS3Bucket: your.bucket.url
    AssetDirectory: directory/where/your/assets/in

### Commands

To upload (Note: it doesn't delete files):

    $ lmdo s3 sync

Environment Variables
------

You can use lmdo to create environment variables utilising `$Stack`, `$Env` or just a string

### Configuration

    EnvExportMap:
      EnvName1: String
      EnvName2: $env|env_name
      EnvName3: $stack|stack-name::key

### Commands

Running `lmdo env export` will produce a string contains all your environment variable defined in `EnvExportMap`. To export to your shell, you need to run:

    $ eval $(lmdo env export)


