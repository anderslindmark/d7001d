from cartype_sqs import deQueue, delMsg
from sql import session, Packet
from time import sleep

while True:
	# Fetch a packet id
	msg = deQueue()
	if msg is None:
		sleep(10)
	else:
		packet_id = None
		try:
			packet_id = int(msg.get_body())
			print "Packet id:", str(packet_id)
		except:
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
		# Check if cartype has been added since the packet was enqueued
		if packet.cartype is None:
			# Calculate cartype
			ctype = packet.getCarType()
			# if ctype is none that means the data was corrupt and the packet was deleted from db
			if ctype is not None:
				session.add(packet)
				session.commit()
		delMsg(msg)
