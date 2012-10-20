import cartype_sqs as sqs
from sql import session, Packet
from time import sleep

while True:
	# Fetch a packet id
	packet_id = sqs.deQueue()
	if packet_id is None:
		sleep(10)
	else:
		# Get that packet from the database
		packet = session.query(Packet).filter(Packet.id == packet_id).one()
		# Check if cartype has been added since the packet was enqueued
		if packet.cartype is None:
			# Calculate cartype
			packet.getCarType()
			session.add(packet)
			sesion.commit()

