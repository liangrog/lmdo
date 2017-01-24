lmdo
=========

*A simple CLI tool for developing microservices using AWS Lambda function (python2.7) and managing logistic of AWS resources*


Purpose
-------

The existing open source tool sets such as
[Apex](https://github.com/apex/apex) and
[Serverless](https://github.com/serverless/serverless) have all sorts
of limitations and too many abstractions. I understand tools are often opinionated but flexibility should be allowed. 

lmdo allows:
- Use cloud formation templates
- Use swagger for API Gateway
- Individually managing AWS resources
- Manage life cycles of AWS Lambda functions
- Bridge Django framework
- Tail Cloudwatch logs

Usage
-----

Installation

    $ sudo pip install lmdo

Create skeleton
    
    $ lmdo tpl

Package and upload Lambda function to S3

    $ lmdo lm

Create/Update CloudFormation and create Lambda function

    $ lmdo cf

Create/update API gateway and deploy stage

    $ lmdo api

Deploy the service in one step
    
    $ lmdo deploy

Delete the service and associated AWS assets

    $ lmdo destroy
