from __future__ import print_function
import sys
import os

from .base import Base
from lmdo.config import tmp_dir, exclude
from lmdo.utils import zipper
from lmdo.oprint import Oprint

class Lm(Base):
    """
    Class packaging Lambda function codes and
    upload it to S3
    """

    def run(self):
        self.s3 = self.get_aws_client('s3')
        self.package()
        self.upload()
        self.cleanup()

    def get_pkg_name(self, file_type='.zip'):
        """
        Construct zip package name
        Package name = username(if any and dev)-stage-service.zip
        """

        surfix = self.config_loader.get_value('Stage') + '-' + self.config_loader.get_value('Service')
        return self.config_loader.get_value('User') + '-' + surfix + file_type

    def get_s3_name(self):
        """
        Construct s3 object name
        """
        
        return self.get_pkg_name()

        # Lambda function s3key doesn't like sub folders
        # It's using reg "^[0-9A-Za-z\.\-_]*(?<!\.)$"
        #surfix = self.config_loader.get_value('Stage')
        #return self.config_loader.get_value('User') + '/' + surfix + '/' + self.get_pkg_name()

    def package(self):
        """
        Create zip package Python Lambda function
        """

        from_path = './'
        target_file_name = tmp_dir + self.get_pkg_name()
    
        return zipper(from_path, target_file_name, exclude)

    def upload(self):
        """
        Upload Lambda package to S3
        """
        
        lambda_bucket = self.config_loader.get_value('LambdaBucketName')

        # Check if bucket exist
        if len(lambda_bucket) > 0:
            if not self.if_bucket_exist(lambda_bucket):
                Oprint.warn('S3 bucket ' + lambda_bucket + " doesn't exist!")
                sys.exit(0)
        # Create a new bucket
        else:
            lambda_bucket = self.get_pkg_name(file_type='') 
            if not self.if_bucket_exist(lambda_bucket):
                self.create_bucket(lambda_bucket)

        Oprint.info('Start uploading ' +  self.get_pkg_name() + ' to S3 bucket ' + self.config_loader.get_value('LambdaBucketName'))

        pkg_path = tmp_dir + self.get_pkg_name()
        with open(pkg_path, 'rb') as outfile:
            self.s3.put_object(Bucket=lambda_bucket, Key=self.get_s3_name(), Body=outfile)

        Oprint.info('Finished uploading ' +  self.get_pkg_name() + ' to S3 bucket ' + self.config_loader.get_value('LambdaBucketName'))

        return True

    def cleanup(self):
        """
        Remove temporary package
        """

        try:
            pkg_path = tmp_dir + self.get_pkg_name()
            os.remove(pkg_path)
        except OSError:
            pass

    def destroy(self):
        """
        Remove package from bucket
        """

        try:
            Oprint.info('Start deleting ' +  self.get_pkg_name() + ' from S3 bucket ' + self.config_loader.get_value('LambdaBucketName'))

            self.s3.delete_object(Bucket=lambda_bucket, Key=self.get_s3_name())

            Oprint.info(self.get_pkg_name() + ' has been deleted from S3 bucket ' + self.config_loader.get_value('LambdaBucketName'))
        except Exception as e:
            Oprint.err(e)
            return False

        return True


