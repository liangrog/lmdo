from __future__ import print_function
import os
import fnmatch

from tqdm import tqdm

from lmdo.cmds.aws_base import AWSBase
from lmdo.oprint import Oprint
from lmdo.utils import sys_pause
from lmdo.waiters.s3_waiters import S3WaiterBucketCreate, S3WaiterBucketDelete, S3WaiterObjectCreate
from lmdo.config import S3_UPLOAD_EXCLUDE

class S3(AWSBase):
    """S3 handler"""
    def __init__(self):
        super(S3, self).__init__()
        self._client = self.get_client('s3') 
        self._resource = self.get_resource('s3')

    @property
    def client(self):
        return self._client

    def sync(self):
        """Sync local asset to s3"""
        if not self._config.get('AssetDirectory') or not self._config.get('AssetS3Bucket'):
            Oprint.err('Your AssetDirectory or AssetS3Bucket is missing from lmdo.yml', 's3')

        files = self.prepare_files_for_upload('./{}'.format(self._config.get('AssetDirectory')), self._config.get('AssetDirectory'), S3_UPLOAD_EXCLUDE)
        for f in files:
            self.upload_file(self._config.get('AssetS3Bucket'), f.get('path'), f.get('key'), ExtraArgs=f.get('extra_args'))

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

    def upload_file(self, bucket_name, file_path, key, **kwargs):
        """Upload file to S3, provide network progress bar"""
        # Check if bucket exist, create one if user agrees
        if not self.if_bucket_exist(bucket_name):
            sys_pause('Bucket {} doesn\'t exist! Do you want to create it? [yes/no]'.format(bucket_name), 's3')
            self.create_bucket(bucket_name)

        Oprint.info('Start uploading {} to S3 bucket {}'.format(key, bucket_name), 's3')
        #waiter = S3WaiterObjectCreate(self._client)
        
        progress = tqdm(total=float(os.stat(file_path).st_size), unit_scale=True, unit='B')
        self._client.upload_file(file_path, bucket_name, key, Callback=progress.update, **kwargs)
        
        #waiter.wait(bucket_name, key)
        Oprint.info('Complete uploading {}'.format(key), 's3')

        return True

    def get_bucket_url(self, bucket_name):
        """fetch s3 bucket url"""
        return 'https://s3.amazonaws.com/{}'.format(bucket_name)

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
                    
    def prepare_files_for_upload(self, from_path, asset_dir, exclude=None):
        """
        Prepare files for uploading
            exclude = {
                'dir': [],
                'file': []
            }
        """
        output = []
        for root, dirs, files in os.walk(from_path):
            if not exclude:
                for f in files:
                    abs_path = os.path.join(root, f)
                    data = {
                        'path': abs_path,
                        'key': os.path.relpath(abs_path, asset_dir)
                    }

                    if f.endswith('.svg'):
                        data['extra_args'] = {'ContentType': 'image/svg+xml'}

                    output.append(data)
            else:
                for f in files:
                    excl = False

                    #check if file/folder should be excluded
                    if exclude['dir']:
                        for ex_dir in exclude['dir']:
                            if fnmatch.fnmatch(root, ex_dir):
                                excl = True
                                break

                    if exclude['file']:
                        for ex_file in exclude['file']:
                            if fnmatch.fnmatch(f, ex_file):
                                excl = True
                                break

                    if not excl:
                        abs_path = os.path.join(root, f)
                        data = {
                            'path': abs_path,
                            'key': os.path.relpath(abs_path, asset_dir)
                        }

                        if f.endswith('.svg'):
                            data['extra_args'] = {'ContentType': 'image/svg+xml'}

                        output.append(data)

        return output


