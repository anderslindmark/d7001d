import random
import sql
import os

# Load all example payloads in 'process64/pkt' and add them to the database

NUM_CELLS = 10
NUM_NODES = NUM_CELLS*10
DATA_PATH = "/home/ubuntu/process64/pkt"
BASETIME = 1350000000

datafiles = os.listdir(DATA_PATH)

while len(datafiles):
	datafile = open(DATA_PATH + "/" + datafiles.pop(), 'rb')
	data = datafile.read()
	datafile.close()

	cell = random.randrange(NUM_CELLS+1)
	node = random.randrange(NUM_NODES+1)
	roadside = random.randrange(2)
	size = len(data)
	timeoffset = random.randrange(9999999)
	time = (BASETIME + timeoffset) * 1000

	packet = sql.Packet(cell, node, roadside, time, size, data)
	sql.session.add(packet)
	sql.session.commit()	


