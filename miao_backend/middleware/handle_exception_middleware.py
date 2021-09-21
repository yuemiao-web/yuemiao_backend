from miao_backend.exceptions import BusinessException
from miao_backend.common.response import GenericResponse
import logging

log = logging.getLogger('log')

class HandleExceptionMiddleware():
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response
    
    @staticmethod
    def process_exception(request, exception):
        log.error(exception, exc_info=True, stack_info=True)
        if isinstance(exception, BusinessException):
            return GenericResponse(code=exception.code, msg=exception.msg)

        return GenericResponse(code=0, msg='未知异常!')