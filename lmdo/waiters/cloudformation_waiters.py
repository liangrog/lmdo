
from lmdo.waiters.cli_waiter_interface import CliWaiterInterface
from lmdo.waiters.aws_waiter_base import AWSWaiterBase
from lmdo.oprint import Oprint
from lmdo.spinner import spinner


class CloudformationWaiterStackCreate(AWSWaiterBase, CliWaiterInterface):
    """Cloudformation waiter for creating stack"""
    def __init__(self, client=None, client_type='cloudformation'):
        super(CloudformationWaiterStackCreate, self).__init__(client=client, client_type=client_type)
        self._client_type = client_type
        self._stack_create = self._client.get_waiter('stack_create_complete')

    def get_waiter(self):
        return self._stack_create

    def wait(self, stack_name):
        try:
            Oprint.info('Start creating stack {}'.format(stack_name), self._client_type)
            spinner.start()
            self._stack_create.wait(StackName=stack_name)
            spinner.stop()
            Oprint.info('Stack {} creation completed'.format(stack_name), self._client_type)
        except Exception as e:
            spinner.stop()

class CloudformationWaiterStackUpdate(AWSWaiterBase, CliWaiterInterface):
    """Cloudformation waiter for updating stack"""
    def __init__(self, client=None, client_type='cloudformation'):
        super(CloudformationWaiterStackUpdate, self).__init__(client=client, client_type=client_type)
        self._client_type = client_type
        self._stack_update = self._client.get_waiter('stack_update_complete')

    def get_waiter(self):
        return self._stack_update

    def wait(self, stack_name):
        try:
            Oprint.info('Start updating stack {}'.format(stack_name), self._client_type)
            spinner.start()
            self._stack_update.wait(StackName=stack_name)
            spinner.stop()
            Oprint.info('Stack {} update completed'.format(stack_name), self._client_type)
        except Exception as e:
            spinner.stop()


class CloudformationWaiterStackDelete(AWSWaiterBase, CliWaiterInterface):
    """Cloudformation waiter for updating stack"""
    def __init__(self, client=None, client_type='cloudformation'):
        super(CloudformationWaiterStackDelete, self).__init__(client=client, client_type=client_type)
        self._client_type = client_type
        self._stack_delete = self._client.get_waiter('stack_delete_complete')

    def get_waiter(self):
        return self._stack_delete

    def wait(self, stack_name):
        try:
            Oprint.info('Start deleting stack {}'.format(stack_name), self._client_type)
            spinner.start()
            self._stack_delete.wait(StackName=stack_name)
            spinner.stop()
            Oprint.info('Stack {} delete completed'.format(stack_name), self._client_type)
        except Exception as e:
            spinner.stop()

class CloudformationWaiterChangeSetCreateComplete(AWSWaiterBase, CliWaiterInterface):
    """Cloudformation waiter for updating stack"""
    def __init__(self, client=None, client_type='cloudformation'):
        super(CloudformationWaiterChangeSetCreateComplete, self).__init__(client=client, client_type=client_type)
        self._client_type = client_type
        self._change_set_create = self._client.get_waiter('change_set_create_complete')

    def get_waiter(self):
        return self._change_set_create

    def wait(self, change_set_name, stack_name):
        try:
            Oprint.info('Start creating change set {} for stack {}'.format(change_set_name, stack_name), self._client_type)
            spinner.start()
            self._change_set_create.wait(StackName=stack_name, ChangeSetName=change_set_name)
            spinner.stop()
            Oprint.info('Change set {} creation completed'.format(change_set_name), self._client_type)
        except Exception as e:
            spinner.stop()


