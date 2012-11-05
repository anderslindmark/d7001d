
class RequestError(Exception):
    def asXML(self, reqID):
		return ""

class StartTimeError(RequestError):
	
	def __init__(self, time, reason="Out of range"):
		self.time = str(time)
		self.reason = reason
	
	def asXML(self, reqID="RequestIDXXXXXXX"):
		return """
<""" + self.id + """>
	<Error>
		<StartTimeError>
			<ErrorData>""" + self.time + """</ErrorData>
			<ErrorDescription>""" + self.reason + """</ErrorDescription>
		</StartTimeError>
	</Error>
</""" + self.id+  ">"

class StopTimeError(RequestError):
    
	def __init__(self, time, reason="Out of range"):
		self.time = str(time)
		self.reason = reason

	def asXML(self, reqID="RequestIDXXXXXXX"):
		return """
<""" + self.id + """>
	<Error>
		<StopTimeError>
			<ErrorData>""" + self.time + """</ErrorData>
			<ErrorDescription>""" + self.reason + """</ErrorDescription>
		</StopTimeError>
	</Error>
</""" + self.id + ">"

class CellIDError(RequestError):
    def __init__(self, cellID, reason="No such cell"):
		self.cellID = cellID
        self.reason = reason
	
	def asXML(self, reqID="RequestIDXXXXXXX"):
		return """
<""" + reqID + """>
	<Error>
		<CellIDError>
			<ErrorData>""" + self.cellID + """</ErrorData>
			<ErrorDescription>""" + self.reason + """</ErrorDescription>
		</CellIDError>
	</Error>
</""" + reqID + ">"

class XMLError(RequestError):
	
    def __init__(self, reason="Error in XML syntax"):
		self.reason = reason

	def asXML(self, reqID="RequestIDXXXXXXX"):
		return """
<""" + reqID + """>
	<Error>
		<XMLError>
			<ErrorDescription>""" + self.reason + """</ErrorDescription>
		</XMLError>
	</Error>
</""" + reqID + ">"


class DataReadTimeoutException(Exception):
	pass

	