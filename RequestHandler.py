import time
import threading
import S3
import Request
from boto.sqs.message import Message
from boto.sqs.connection import SQSConnection
import aws_common
from boto.sqs import regions
from error import XMLError

class RequestHandler(threading.Thread):

    def __init__(self, inQueue, outQueue):
        threading.Thread.__init__(self)
        self.inQueue = inQueue
        self.outQueue = outQueue
    
    def handleMessage(self, message):
        
        body = message.get_body()
        
        try:
            # Parse the request
            request = Request.Request(body)
        except XMLError:
            # Just return if the request can't be parsed
            # This throws away the request
            return
        
        # Process the request
        # If an exception is thrown (other than our RequestErrors),
        # the message will remain in the queue to be processed again later.
        # Corrupt data is removed before the exception is raised, so the
        # request will (hopefully) succeed next time
		# TODO Add TTL to requests, process max 3 times, or something
        reply = request.process()
        
        # Write the reply to S3
        url = S3.uploadFile(request.id + '.xml', reply)
        
        # Put the url to the reply in the outqueue
        m = Message()
        m.set_body(url)
        outQueue.write(m)

	
    def run(self):
        while True:
            # Read a message from the queue and hide it for 10 minutes (should be shorter)
            message = inQueue.read(600)
            if message is not None:
                try:
                    self.handleMessage(message)
                    inQueue.delete_message(message)
                except:
                    pass
                    # Do nothing here, just try another message from the queue
			# Sleep a short while between reads 
            time.sleep(2)


if __name__ == "__main__":

    eu_region = None
    for region in regions():
        if region.name == 'eu-west-1':
            eu_region = region
            break
    print eu_region
    
    # Get the queues (TODO move the queue names to aws_common)
    conn = SQSConnection(aws_access_key_id=aws_common.AWS_ACCESS_KEY,
                         aws_secret_access_key=aws_common.AWS_SECRET_KEY,
                         region=eu_region)
    inQueue = conn.create_queue("12_LP1_SQS_D7001D_jimnys-8_frontend-in")
    outQueue = conn.create_queue("12_LP1_SQS_D7001D_jimnys-8_frontend-out")

    # Start a request handler
    requestHandler = RequestHandler(inQueue, outQueue)
    requestHandler.start()
    
    



