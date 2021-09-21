from django.http import JsonResponse

class GenericResponse(JsonResponse):
    def __init__(self, data: any=None, code=200, msg='操作成功!', **kwargs) -> None:
        d = {
            'code': code,
            'msg': msg,
            'data': data
        }
        super().__init__(d, safe=False, **kwargs)