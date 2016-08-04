
class SiphonClientException(Exception):
    pass

class SiphonCommandException(SiphonClientException):
    pass

class SiphonAPIException(SiphonClientException):
    pass

class SiphonBundlerException(SiphonClientException):
    pass
