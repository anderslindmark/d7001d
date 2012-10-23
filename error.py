
class RequestError(Exception):
    pass

class StartTimeError(RequestError):
    pass

class StopTimeError(RequestError):
    pass

class CellIDError(RequestError):
    pass

class XMLError(RequestError):
    def __init__(self, reqID=''):
        self.reqID = reqID

class DataReadTimeoutException(Exception):
	pass
