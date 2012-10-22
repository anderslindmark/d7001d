import time
import threading
import S3
import Request
from boto.sqs.message import Message
from boto.sqs.connection import SQSConnection
import aws_common
from boto.sqs import regions

if __name__ == "__main__":

    eu_region = None
    for region in regions():
        if region.name == REGION:
            eu_region = region
            break
    print eu_region
    
    conn = SQSConnection(aws_access_key_id=aws_common.AWS_ACCESS_KEY,
                         aws_secret_access_key=aws_common.AWS_SECRET_KEY,
                         region=eu_region)
    inQueue = conn.create_queue("12_LP1_SQS_D7001D_jimnys-8_frontend-in")
    # outQueue = conn.create_queue("frontendOutQueue")

    for i in range(1, 5):
        m = Message()
        m.set_body(open('test' + str(i) + '.xml', 'r').read())
        print m.get_body()
        status = inQueue.write(m)
    
    
    



