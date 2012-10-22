import time
import threading
import S3
import Request
from boto.sqs.message import Message
from boto.sqs.connection import SQSConnection
import aws_common
from boto.sqs import regions

class RequestHandler(threading.Thread):

    def __init__(self, inQueue, outQueue):
        threading.Thread.__init__(self)
        self.inQueue = inQueue
        self.outQueue = outQueue
    
    def handleMessage(self, message):
        body = message.get_body()
        request = Request.Request(body)
        reply = request.process()
        
        #print reply
        
        # Write to S3
        url = S3.uploadFile(request.id, reply)
        
        #print url
        m = Message()
        m.set_body(url)
        outQueue.write(m)

    def run(self):
        while True:
            message = inQueue.read()
            if message is not None:
                inQueue.delete_message(message)
                self.handleMessage(message)
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
    for i in range(1, 6):
        requestHandler = RequestHandler(inQueue, outQueue)
        requestHandler.start()
    
    



