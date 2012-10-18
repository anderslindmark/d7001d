from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import and_
from sqlalchemy import Column, Integer, VARCHAR, DateTime, BLOB, SmallInteger
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from tempfile import mkdtemp
import dateutil.parser
import rawdata
import aws_common

DB_DEBUG = True

Base = declarative_base()
class Packet(Base):
	__tablename__ = "packets"

	id = Column(Integer, primary_key=True)
	cell_id = Column(SmallInteger)
	node_id = Column(SmallInteger)
	cartype = Column(VARCHAR(length=2))
	road_side = Column(SmallInteger)
	timestamp = Column(DateTime)
	raw_data = Column(BLOB)
	raw_data_size = Column(Integer)

	def __init__(self, cell_id, node_id, road_side, timestamp, raw_data_size, raw_data):
		self.cell_id = cell_id
		self.node_id = node_id
		self.road_side = road_side
		# Timestamp is in ms since epoch.
		t = datetime.fromtimestamp(timestamp/1000)
		self.timestamp = t.strftime("%Y-%m-%d %H:%M:%S")
		self.raw_data_size = raw_data_size
		self.raw_data = raw_data
		self.cartype = rawdata.getCarType(raw_data)

	def __repr__(self):
		return "<Packet('%d', '%d', '%s', '*DATA*', '%s', '%s')>" % (self.cell_id, self.node_id, self.timestamp, self.raw_data_size, self.cartype)

	@staticmethod
	def _fixTimes(time):
		"""
		Check if time was sent in the correct format, if not: try to convert it. 
		Works like this: (input -> output)
		201210172142		-> 2012-10-17 21:42:00
		20121017214212		-> 2012-10-17 21:42:12
		2012-10-17 2142		-> 2012-10-17 21:42:00
		2012-10-17 21:42	-> 2012-10-17 21:42:00
		2012-10-17 21:42:12 -> 2012-10-17 21:42:12
		"""
		t = None
		try:
			t = datetime.strptime(time, "%Y-%m-%d %H:%M:%S")
		except ValueError:
			t = dateutil.parser.parse(time)
			print "Date was not in the correct format. Interpreting it as: %s" % t.strftime("%Y-%m-%d %H:%M:%S")
		return t.strftime("%Y-%m-%d %H:%M:%S")
		

	@staticmethod
	def fetchInterval(cell_id, startTime, stopTime):
		startTime = Packet._fixTimes(startTime)
		stopTime = Packet._fixTimes(stopTime)
		l = []
		for packet in session.query(Packet).filter(and_(Packet.cell_id == cell_id, Packet.timestamp.between(startTime, stopTime))).order_by(Packet.timestamp):
			l.append(packet)
		return l

	@staticmethod
	def writeFiles(packets):
		tempdir = mkdtemp()
		i = 0
		files = []
		for packet in packets:
			filename = tempdir + '/' + str(i)
			f = open(filename, 'wb')
			f.write(packet.raw_data)
			f.close()
			files.append(filename)
		return (tempdir, files)

	@staticmethod
	def listAllCells():
		ids = set()
		result = session.query(Packet.cell_id).all()
		for row in result:
			ids.add(row.cell_id)
		return ids

# To create the table; first drop existing table if any and then
#  Packet.metadata.create_all(engine)

ENGINE_STRING = "mysql://" + aws_common.DB_USER + ':' + aws_common.DB_PASSWORD + '@' + aws_common.DB_ADDRESS + '/' + aws_common.DB_DATABASE

engine = create_engine(ENGINE_STRING, echo=DB_DEBUG)

Session = sessionmaker(bind=engine)
session = Session()

if __name__ == "__main__":
	p = Packet(2, 3, 0, 1350555611626, 8, "rawdata2")
	##session.add(p)
	##session.commit()
	
	# Incoming packets from the Sensor Network
	#  import sql
	#  cell_id, node_id, timestamp, rawdata = recievePacket()
	#  p = sql.Packet(cell_id, node_id, timestamp, rawdata)
	#  sql.session.add(p)
	#  sql.session.commit()
	# Done.

	# Requests from the front-end
	#  from sql import Packet
	#  import rawdata
	#  import S3
	#  packets = Packet.fetchInterval(startTime, stopTime)
	#  path, files = Packet.writeFiles(packets)
	#  avgSpeed = rawdata.getAvgSpeed(path, files)
	# Get XML strings etc
	#  url = S3.uploadFile(filnamn, xmltext)
	# Done.


