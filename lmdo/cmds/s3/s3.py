from __future__ import print_function
import os
import fnmatch

from tqdm import tqdm

from lmdo.cmds.aws_base import AWSBase
from lmdo.oprint import Oprint
from lmdo.utils import sys_pause
from lmdo.waiters.s3_waiters import S3WaiterBucketCreate, S3WaiterBucketDelete 

class S3(AWSBase):
    """S3 handler"""
    def __init__(self):
        super(S3, self).__init__()
        self._client = self.get_client('s3') 
        self._resource = self.get_resource('s3')

    @property
    def client(self):
        return self._client
                   
    def if_bucket_exist(self, bucket_name):
        """Check if bucket exist"""
        if self._resource.Bucket(bucket_name) in self._resource.buckets.all():
            return True
        return False

    def create_bucket(bucket_name, acl='private'):
        """Create private bucket"""
        waiter = S3WaiterBucketCreate(self._client)
        self._client.create_bucket(ACL=acl, Bucket=bucket_name, CreateBucketConfiguration={'LocationConstraint': self.get_region()})
        waiter.wait(Bucket=bucket_name)

        return True

    def delete_bucket(bucket_name):
        """Remove private bucket"""
        waiter = S3WaiterBucketDelete(self._client)
        self._client.delete_bucket(Bucket=bucket_name)
        waiter.wait(Bucket=bucket_name)
        
        return True

    def upload_file(self, bucket_name, key, file_path):
        """Upload file to S3, provide network progress bar"""
        # Check if bucket exist, create one if user agrees
        if not self.if_bucket_exist(bucket_name):
            sys_pause('Bucket {} doesn\'t exist! Do you want to create it? [yes/no]'.format(bucket_name), 's3')
            self.create_bucket(bucket_name)

        Oprint.info('Start uploading {} to S3 bucket {}'.format(key, bucket_name), 's3')

        progress = tqdm(total=float(os.stat(pkg_path).st_size), unit_scale=True, unit='B')

        self.s3.upload_file(file_path, bucket_name, key, Callback=progress.update)

        Oprint.info('Complete uploading {} to S3 bucket {}'.format(key, bucket_name), 's3')

        return True

    def get_bucket_url(self, bucket_name):
        """fetch s3 bucket url"""
        return '{}.s3.amazonaws.com'.format(bucket_name)

    def delete_bucket_object(self, bucket_name):
        """
        Delete all object under a bucket so
        the bucket can be deleted during stack
        removal
        """
        try:
            objects = self._client.list_objects_v2(Bucket=bucket)
            self._client.delete_objects(Bucket=bucket, Delete={'Objects': objects['Contents']})
        except Exception as e:
            Oprint.err(e, 's3')
                    

