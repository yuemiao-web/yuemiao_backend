class BusinessException(Exception):
    def __init__(self, code, msg, *args: object) -> None:
        super().__init__(*args)

        self.code = code
        self.msg = msg
    
    def __str__(self) -> str:
        return f'出现业务异常: {self.msg}'