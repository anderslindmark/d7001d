from boto.sqs.connection import SQSConnection
from boto.sqs import regions
from boto.sqs.message import Message
import aws_common

eu_region = None
for region in regions():
	if region.name == 'eu-west-1':
		eu_region = region
		break

sqs_connection = SQSConnection(aws_common.AWS_ACCESS_KEY, aws_common.AWS_SECRET_KEY, region=eu_region)
q = sqs_connection.create_queue('12_LP1_SQS_D7001D_anelit-4-ctype', 120)


def enQueue(packetId):
	m = Message(body=str(packetId))
	q.write(m)

def deQueue():
	msglist = sqs_connection.receive_message(q)
	if not len(msglist) == 1:
		return None
	msg = msglist[0]
	return msg

def delMsg(msg):
	sqs_connection.delete_message(q, msg)
