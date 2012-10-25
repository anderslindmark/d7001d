from cartype_sqs import deQueue, delMsg
from sql import session, Packet
from time import sleep

"""
This process is meant to run in the background on any suitable server.
It fetches unprocessed packets from the sqs queue that contains incoming packets 
and calculates cartype.
"""

while True:
	# Fetch a packet id
	msg = deQueue()
	if msg is None:
		# No packets on queue
		sleep(10)
	else:
		# Get packet id from the queue
		packet_id = None
		try:
			packet_id = int(msg.get_body())
			print "Packet id:", str(packet_id)
		except:
			# If the message doesn't contain an integer (i.e someone put something on the queue that doesnt belong there)
			print "Erroneous msg"
			delMsg(msg)
			continue
		# Get that packet from the database
		try:
			packet = session.query(Packet).filter(Packet.id == packet_id).one()
		except:
			# Packet has been removed from db since it was added to the queue
			delMsg(msg)
			continue
		# Check if cartype has been added since the packet was enqueued (i.e packet.cartype != None)
		if packet.cartype is None:
			# Calculate cartype
			ctype = packet.getCarType()
			# if ctype is None that means the data was corrupt and the packet was deleted from db by the call to getCarType()
			if ctype is not None:
				session.add(packet)
				session.commit()
		delMsg(msg)
