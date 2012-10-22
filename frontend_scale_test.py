import time
import threading
import S3
import Request
from boto.sqs.message import Message
from boto.sqs.connection import SQSConnection
import aws_common
from boto.sqs import regions

import xml.etree.ElementTree as ET

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
    # outQueue = conn.create_queue("frontendOutQueue")

    types = ['ListCells', 'CellStatNet', 'CellStatSpeed']

    for i in range(0, 100):
        
        root = ET.Element('RequestID' + str(5 + i))
        eType = ET.SubElement(root, 'RequestType')
        eType.text = types[i % len(types)]
        eId = ET.SubElement(root, 'CellID')
        eId.text = str(i % 11) # Existing cell ids = [0, 10]
        eStart = ET.SubElement(root, 'TimeStart')
        eStart.text = '201201011200'
        eStop = ET.SubElement(root, 'TimeStop')
        eStop.text = '201301011200'
        
        m = Message()
        m.set_body(ET.tostring(root))
        print m.get_body()
        status = inQueue.write(m)
    
    
    



