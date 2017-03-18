

class CfStatus(object):
    """CloudFormation lmdo status mapping"""
    STACK_COMPLETE = "complete"
    STACK_FAILED = "failed"
    STACK_IN_PROGRESS = "in progress"

    CHANGE_SET_PENDING = "pending"
    CHANGE_SET_READY = "ready"
    CHANGE_SET_DEFUNCT = "defunct"
