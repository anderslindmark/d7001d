import time
import threading
import S3
import Request
from boto.sqs.message import Message
from boto.sqs.connection import SQSConnection
import aws_common

if __name__ == "__main__":

    conn = SQSConnection(aws_common.AWS_ACCESS_KEY, aws_common.AWS_SECRET_KEY)
    inQueue = conn.create_queue("frontendInQueue")
    outQueue = conn.create_queue("frontendOutQueue")

    for i in range(1, 5):
        m = Message()
        m.set_body(open('test' + str(i) + '.xml', 'r').read())
        print m.get_body()
        status = inQueue.write(m)
    
    
    



