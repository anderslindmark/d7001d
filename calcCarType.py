from sql import session, Packet
from time import sleep

# TODO: Instead of fetching all cartype==null packets, push all incoming packets onto an SQS-queue
#		and have this script fetch from that queue. This way it will scale better.

while True:
	# Get a list of all packets where cartype is not yet calculated
	packetlist = session.query(Packet).filter(Packet.cartype == None).all()
	for packet in packetlist:
		packet.getCarType()
		session.add(packet)
	session.commit()

	if len(packetlist) == 0:
		# Dont spam the database
		sleep(10)

