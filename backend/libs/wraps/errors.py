class SerializerError(Exception):
    def __init__(self, msg: str, code: int):
        self.code = code
        self.msg = msg
