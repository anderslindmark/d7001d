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
            request = Request.Request(body)
        except XMLError:
            return
        
        reply = request.process()
        
        #print reply
        
        # Write to S3
        url = S3.uploadFile(request.id + '.xml', reply)
        
        #print url
        m = Message()
        m.set_body(url)
        outQueue.write(m)

    def run(self):
        while True:
            message = inQueue.read(600)
            if message is not None:
                try:
                    self.handleMessage(message)
                    inQueue.delete_message(message)
                except:
                    pass
                    # Do nothing here, just try another message from the queue
                    # TODO Delete message from the queue? And maybe the corrupt packet from the db
            #Sleep maybe?
            time.sleep(2)


if __name__ == "__main__":

    eu_region = None
    for region in regions():
        if region.name == 'eu-west-1':
            eu_region = region
            break
    print eu_region
    
    conn = SQSConnection(aws_access_key_id=aws_common.AWS_ACCESS_KEY,
                         aws_secret_access_key=aws_common.AWS_SECRET_KEY,
                         region=eu_region)
    inQueue = conn.create_queue("12_LP1_SQS_D7001D_jimnys-8_frontend-in")
    outQueue = conn.create_queue("12_LP1_SQS_D7001D_jimnys-8_frontend-out")

    # Start five threads with request handlers
    # for i in range(1, 6):
    requestHandler = RequestHandler(inQueue, outQueue)
    requestHandler.start()
    
    



