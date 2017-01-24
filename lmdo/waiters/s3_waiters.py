
from lmdo.waiters.cli_waiter_interface import CliWaiterInterface
from lmdo.waiters.aws_waiter_base import AWSWaiterBase
from lmdo.oprint import Oprint
from lmdo.spinner import spinner


class S3WaiterBucketCreate(AWSWaiterBase, CliWaiterInterface):
    """S3 waiter for bucket creation"""
    def __init__(self, client=None, client_type='s3'):
        super(S3WaiterBucketCreate, self).__init__(client=client, client_type=client_type)
        self._client_type = client_type
        self._bucket_exists = self._client.get_waiter('bucket_exists')

    def get_waiter(self):
        return self._bucket_exists

    def wait(self, bucket_name):
        try:
            Oprint.info('Bucket {} creation starts'.format(bucket_name), self._client_type)
            spinner.start()
            self._bucket_exist.wait(Bucket=bucket_name)
            spinner.stop()
            Oprint.info('Bucket {} creation completed'.format(bucket_name), self._client_type)
        except Exception as e:
            spinner.stop()


class S3WaiterBucketDelete(AWSWaiterBase, CliWaiterInterface):
    """S3 waiter for bucket delete"""
    def __init__(self, client=None, client_type='s3'):
        super(S3WaiterBucketDelete, self).__init__(client=client, client_type=client_type)
        self._client_type = client_type
        self._bucket_not_exists = self._client.get_waiter('bucket_not_exists')

    def get_waiter(self):
        return self._bucket_not_exists

    def wait(self, bucket_name):
        try:
            Oprint.info('Bucket {} delete starts'.format(bucket_name), self._client_type)
            spinner.start()
            self._bucket_not_exist.wait(Bucket=bucket_name)
            spinner.stop()
            Oprint.info('Bucket {} delete completed'.format(bucket_name), self._client_type)
        except Exception as e:
            spinner.stop()


class S3WaiterObjectCreate(AWSWaiterBase, CliWaiterInterface):
    """S3 waiter for object create"""
    def __init__(self, client=None, client_type='s3'):
        super(S3WaiterObjectCreate, self).__init__(client=client, client_type=client_type)
        self._client_type = client_type
        self._object_exists = self._client.get_waiter('object_exists')

    def get_waiter(self):
        return self._object_exists

    def wait(self, bucket_name, key, **kwargs):
        try:
            Oprint.info('Object {} creation in bucket {} starts'.format(key, bucket_name), self._client_type)
            #spinner.start()
            self._object_exist.wait(Bucket=bucket_name, key=key, **kwargs)
            #spinner.stop()
            Oprint.info('Object {} creation completed'.format(key), self._client_type)
        except Exception as e:
            spinner.stop()


class S3WaiterObjectDelete(AWSWaiterBase, CliWaiterInterface):
    """S3 waiter for object delete"""
    def __init__(self, client=None, client_type='s3'):
        super(S3WaiterObjectDelete, self).__init__(client=client, client_type=client_type)
        self._client_type = client_type
        self._object_not_exists = self._client.get_waiter('object_not_exists')

    def get_waiter(self):
        return self._object_not_exists

    def wait(self, bucket_name, key, **kwargs):
        try:
            Oprint.info('Object {} delete in bucket {} starts'.format(key, bucket_name), self._client_type)
            spinner.start()
            self._object_not_exist.wait(Bucket=bucket_name, key=key, **kwargs)
            spinner.stop()
            Oprint.info('Object {} delete in bucket {} completed'.format(key, bucket_name), self._client_type)
        except Exception as e:
            spinner.stop()



