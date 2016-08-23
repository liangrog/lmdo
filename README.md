lmdo
=========

*A simple CLI tool for developing microservices using AWS Lambda*


Purpose
-------

The existing open source tool sets such as [Apex](https://github.com/apex/apex) and  [Serverless](https://github.com/serverless/serverless) bear all sort
of limitations and too much abstractions, preventing the flexibility of utilising
AWS cloudformation and other resources.

lmdo allows:

- Customizing cloud formation template
- Utilising Lambda function for queries to other AWS resources
- Working in a team environment
- Passing in parameters to cloud formation template

Usage
-----

Installation

    $ pip install .

Create skeleton
    
    $ lmdo tpl

Pakaging and upload Lambda function to S3

    $ lmdo lm

Create/Update cloud formation and create Lambda function

    $ lmdo cf

Create/update API gateway and deploy stage

    $ lmdo api

Deploy the whole service
    
    $ lmdo deploy

Delete the service and associate AWS assets

    $ lmdo destroy
