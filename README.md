lmdo
=========

*A simple CLI tool for developing microservices using AWS Lambda*


Purpose
-------

The existing open source tool sets such as
[Apex](https://github.com/apex/apex) and
[Serverless](https://github.com/serverless/serverless) have all sorts
of limitations and too many abstractions, preventing the flexibility
of utilising AWS CloudFormation and other resources.

lmdo allows:

- Customizing cloud formation templates
- Utilising Lambda functions for queries to other AWS resources
- Working in a team environment
- Passing in parameters to CloudFormation templates

Usage
-----

Installation

    $ pip install .

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
