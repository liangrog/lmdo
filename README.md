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
- Offer two type of managed Lambda functions: wsgi and CloudWatch Event scheduler dispatcher
- CloudWatch log output on CL

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

    **Note**: If explicitly using config options `Region, AWSKey, AWSSecret`, it's recommended to define them in the environment. Using syntax like `$env|YOUR_ENV_VAR` lmdo will replace them with the value.

2. Other mandatory configuration Options

    `Service`: The name of your service/project

    `User`: The user that deploys the service/project

    `Stage`: The deployment stage


One Step Deployment
-------------------
To deploy your entire service, run:

    $ lmdo deploy

To delete, run:

    $ lmdo destroy


CloudFormation
--------------
### Available reserved utility variables
They will be replaced with correct value during deployment

    $env|ENV_VAR_NAME: Environment variables

    $template|template-file-name: Nested stack template to be used to construct proper S3 bucket url for stack resource `TemplateURL`

    $stack|stack-name::output-key: The value of an existing stack's output based on key name. **Note**: the stack referring to must exist before deployment.

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

    c. Using syntax like `TemplateURL: $template|your-nested-stack-template-file-name` in your master template stack resource, lmdo will replace the syntax to appropriate S3 url.

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

### Commands

To create your CloudFormation, run:

    $ lmdo cf create

To update or delete, run the similar command using `update` or `delete` keyword

To use change-set instead of directly update stack, use `-c` or `--change_set` option:

    $ lmdo cf create -c

For output stack event during process, use `-e` or `--event` option:

    $ lmdo cf create -e

