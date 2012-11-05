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

    m = Message()
    m.set_body("""
        <RequestIDCellIDError>
        <RequestType>CellStatNet</RequestType>
        <TimeStart>201201011230</TimeStart>
        <TimeStop>201301011250</TimeStop>
        <CellID>129129</CellID>
        </RequestIDCellIDError>""")
    status = inQueue.write(m)

    m = Message()
    m.set_body("""
        <RequestIDStartTimeError>
        <RequestType>CellStatNet</RequestType>
        <TimeStart>smurf</TimeStart>
        <TimeStop>201301011250</TimeStop>
        <CellID>1</CellID>
        </RequestIDStartTimeError>""")
    status = inQueue.write(m)

    m = Message()
    m.set_body("""
        <RequestIDStopTimeError>
        <RequestType>CellStatNet</RequestType>
        <TimeStart>201201011230</TimeStart>
        <TimeStop>smurf</TimeStop>
        <CellID>1</CellID>
        </RequestIDStopTimeError>""")
    status = inQueue.write(m)

    m = Message()
    m.set_body("""
        <RequestIDXMLError>
        <RequestType>CellStatNet</RequestType>
        <TimeStrt>201201011230</TimeStart>
        <TimeStop>smurf</TimeStop>
        <CellID>1</CellID>
        </RequestIDXMLError>""")
    status = inQueue.write(m)
    
    
    



