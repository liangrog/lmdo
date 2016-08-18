from __future__ import print_function
import sys
import getpass

from .base import Base
from lmdo.config import tmp_dir, exclude
from lmdo.utils import zipper


class Lm(Base):
    """
    Class packaging Lambda function codes and
    upload it to S3
    """

    def run(self):
        self.s3 = self.get_aws_client('s3')
        self.package()
        self.upload()

    def get_pkg_name(self, file_type='.zip'):
        """
        Construct zip package name
        Package name = username(if any and dev)-stage-service.zip
        """

        surfix = self.config_loader.get_value('Stage') + '-' + self.config_loader.get_value('Service')

        if self.config_loader.get_value('Environment') == 'development':
            if len(self.config_loader.get_value('User')) > 0:
                return self.config_loader.get_value('User') + '-' + surfix + file_type
            else:
                return getpass.getuser() + '-' + surfix + file_type
        else:
            return surfix + file_type

    def get_s3_name(self):
        """
        Construct s3 object name
        """

        surfix = self.config_loader.get_value('Stage')
        if self.config_loader.get_value('Environment') == 'developement':
            if len(self.config_loader.get_value('User')) > 0:
                return self.config_loader.get_value('User') + '/' + surfix + '/' + self.get_pkg_name()
        else:
            return surfix + '/' + get_pkg_name()

    def package(self):
        """
        Create zip package Python Lambda function
        """

        from_path = './'
        target_file_name = tmp_dir + self.get_pkg_name()
    
        return zipper(from_path, target_file_name, config.exclude)

    def upload(self):
        """
        Upload Lambda package to S3
        """
        
        lambda_bucket = self.config_loader.get_value('LambdaBucketName')

        # Check if bucket exist
        if len(lambda_bucket) > 0:
            if not self.if_bucket_exist('LambdaBucketName'):
                print('S3 bucket ' + lambda_bucket + " doesn't exist!")
                sys.exit(0)
        # Create a new bucket
        else:
            lambda_bucket = self.get_pkg_name(file_type='') 
            if not self.if_bucket_exist(lambda_bucket)
                self.create_bucket(lambda_bucket)

        print('Start uploading ' +  self.get_pkg_name() + ' to S3 bucket ' + self.config_loader.get_value('LambdaBucketName'))

        pkg_path = tmp_dir + self.get_pkg_name()
        with open(pkg_path, 'rb') as outfile:
            self.s3.put_object(Bucket=lambda_bucket, Key=self.get_s3_name(), Body=outfile)

        print('Finished uploading ' +  self.get_pkg_name() + ' to S3 bucket ' + self.config_loader.get_value('LambdaBucketName'))

        return True
 
