import time
import threading
import S3
import Request
from boto.sqs.message import Message
from boto.sqs.connection import SQSConnection

class RequestHandler(threading.Thread):

    def __init__(self, inQueue, outQueue):
        threading.Thread.__init__(self)
        self.inQueue = inQueue
        self.outQueue = outQueue
    
    def handleMessage(self, message):
        body = message.get_body()
        request = Request.Request(body)
        reply = request.process()
        
        print reply
        
        # Write to S3
        url = S3.uploadFile(request.id, reply)
        
        print url
        
        m = Message()
        m.set_body(url)
        outQueue.write(m)

    def run(self):
        while True:
            messages = inQueue.get_messages()
            if (len(messages) > 0):
                self.handleMessage(messages[0])
                inQueue.delete_message(messages[0])
            #Sleep maybe?
            time.sleep(2)

# The main method
if __name__ == "__main__":

    conn = SQSConnection('AKIAJJNNA44AWFOJ2PSA', '+mIhuaY8n6kEoJJ9rZjyMk2aMP0/2Se3c9kiCyx9')
    inQueue = conn.create_queue('frontendInQueue')
    outQueue = conn.create_queue('frontendOutQueue')

    requestHandler = RequestHandler(inQueue, outQueue)
    requestHandler.start()

    m = Message()
    m.set_body(open('test3.xml', 'r').read())
    print m.get_body()
    status = inQueue.write(m)

#    for i in range(1, 5):
#        m = Message()
#        m.set_body(open('test' + str(i) + '.xml', 'r').read())
#        print m.get_body()
#        status = inQueue.write(m)
#    
#    requestHandler1 = RequestHandler(inQueue, outQueue)
#    requestHandler1.start()
#
#    requestHandler2 = RequestHandler(inQueue, outQueue)
#    requestHandler2.start()

    
    
    



