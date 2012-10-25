from boto.sqs.connection import SQSConnection
from boto.sqs import regions
from boto.sqs.message import Message
import aws_common

"""
Module for communicating with the cartype sqs-queue.
"""

# Get the eu-region
eu_region = None
for region in regions():
	if region.name == 'eu-west-1':
		eu_region = region
		break

# Setup the sqs-connection
sqs_connection = SQSConnection(aws_common.AWS_ACCESS_KEY, aws_common.AWS_SECRET_KEY, region=eu_region)
q = sqs_connection.create_queue('12_LP1_SQS_D7001D_anelit-4-ctype', 120)


def enQueue(packetId):
	"""
	Place a message on the queue
	"""
	m = Message(body=str(packetId))
	q.write(m)

def deQueue():
	"""
	Get a message from the queue
	"""
	msglist = sqs_connection.receive_message(q)
	if not len(msglist) == 1:
		return None
	msg = msglist[0]
	return msg

def delMsg(msg):
	"""
	Delete the message from the queue so it doesn't reappear after the flight-time expires
	"""
	sqs_connection.delete_message(q, msg)

def wipeQueue():
	"""
	Remove all messages from the queue
	"""
	q.clear()
