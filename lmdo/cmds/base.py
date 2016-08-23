from __future__ import print_function
import hashlib

import boto3
from lmdo.cloader import CLoader


class Base(object):
    """
    Command base class
    """

    def __init__(self, options, *args, **kwargs):
        self.options = options
        self.args = args
        self.kwargs = kwargs
        self.config_loader = CLoader() #load global config for all commands

    def get_aws_profile(self):
        """
        Fetch AWS profile
        """

        return self.config_loader.get_value('Profile')

    def get_aws_session(self):
        """
        Fetch boto3 session
        """

        return boto3.Session(profile_name=self.get_aws_profile())

    def get_aws_region(self):
        """
        Get region name from AWS profile
        """

        return self.get_aws_session().region_name

    def get_aws_client(self, client_type):
        """
        Fetch AWS service client
        """

        return self.get_aws_session().client(client_type)

    def get_aws_resource(self, src_type):
        """
        Fetch AWS service resource
        """

        return self.get_aws_session().resource(src_type)

    def if_bucket_exist(self, bucket_name):
        """
        Check if bucket exist
        """

        s3 = self.get_aws_resource('s3')
        if s3.Bucket(bucket_name) in s3.buckets.all():
            return True
        return False

    def create_bucket(bucket_name, acl='private'):
        """
        Create private bucket
        """

        s3 = self.get_aws_resource('s3')
        waiter = self.get_aws_client('s3').get_waiter('bucket_exists')

        s3.create_bucket(ACL=acl, Bucket=bucket_name, CreateBucketConfiguration={'LocationConstraint': self.get_aws_region()})
        print('S3 Bucket ' + bucket_name + ' is being created...')
        waiter.wait(Bucket=bucket_name)
        print('S3 Bucket ' + bucket_name + ' has been credated')

        return True

    def remove_bucket(bucket_name):
        """
        Remove private bucket
        """

        s3 = self.get_aws_resource('s3')
        waiter = self.get_aws_client('s3').get_waiter('bucket_not_exists')
        
        s3.delete_bucket(Bucket=bucket_name)
        print('S3 Bucket ' + bucket_name + ' is being delete...')
        waiter.wait(Bucket=bucket_name)
        print('S3 Bucket ' + bucket_name + ' has been deleted')
        
        return True

    def if_stack_exist(self, stack_name):
        """
        Check if given stack exist
        """

        if not self.cf:
            self.cf = self.get_aws_client('cloundformation')

        try:
            response = self.cf.describe_stacks(StackName=stack_name)
        except Exception as e:
            return False
        
        return True

    def update_stack(self, stack_name, template_body, capabilities='CAPABILITY_NAMED_IAM', **kwargs):
        update = False
        if self.if_stack_exist(stack_name):
            update = True

        if not self.cf
            self.cf = self.get_aws_client('cloundformation')

        try:
            if not update:
                waiter = self.cf.get_waiter('stack_create_complete')

                response = self.cf.create_stack(
                    StackName=stack_name,
                    TemplateBody=template_body,
                    Capabilities=capabilities,
                    Parameters=kwargs['parameters']
                    )

                print('Waiting for new stack ' + stack_name + ' to be created...')
                waiter.wait(StackName=stack_name)
                print('New stack ' + stack_name + ' has been created')
            else:
                waiter = self.cf.get_waiter('stack_update_complete')

                response = self.cf.update_stack(
                    StackName=stack_name,
                    TemplateBody=template_body,
                    Capabilities=capabilities,
                    Parameters=kwargs['parameters']
                    )

                print('Waiting for stack ' + stack_name + ' to be updated...')
                waiter.wait(StackName=stack_name)
                print('Stack ' + stack_name + ' update has been completed')
        except Exception as e:
            print(e)
            return False

        return True

    def remove_stack(self, stack_name):
        """
        Remove a stack by given name
        """

        if not self.cf:
            self.cf = self.get_aws_client('cloudformation')

        try:
            waiter = self.cf.get_waiter('stack_delete_complete')

            response = self.cf.delete_stack(StackName=stack_name)

            print('Waiting for stack ' + stack_name + ' to be deleted...')
            waiter.wait(StackName=stack_name)
            print('Stack ' + stack_name + ' has been deleted')
        except Exception as e:
            print(e)
            return False
        
        return True

    def hashing(content):
        """
        MD5 hasing
        """

        m = hashlib.md5()
        m.update(content)
        return m.hexdigest()

    def run(self):
        """
        Command interface
        """

        raise NotImplementedError('You must implement the run() method!')

