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
from cartype_sqs import enQueue
from error import StartTimeError, StopTimeError, CellIDError

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

	def __init__(self, cell_id, node_id, road_side, timestamp, raw_data_size, raw_data, commit=True):
		self.cell_id = cell_id
		self.node_id = node_id
		self.road_side = road_side
		# Timestamp is in ms since epoch.
		t = datetime.fromtimestamp(timestamp/1000)
		self.timestamp = t.strftime("%Y-%m-%d %H:%M:%S")
		self.raw_data_size = raw_data_size
		self.raw_data = raw_data
		#self.cartype = rawdata.getCarType(raw_data)
		self.cartype = None

		if commit:
			# Commit right away so that p.id is available and can be placed onto queue
			if self.timestamp < first_timestamp:
				first_timestamp = self.timestamp
			if self.timestamp > last_timestamp:
				last_timestamp = self.timestamp
			session.add(self)
			session.commit()
			enQueue(self.id)


	def __repr__(self):
		return "<Packet('%d', '%d', '%s', '*DATA*', '%s', '%s')>" % (self.cell_id, self.node_id, self.timestamp, self.raw_data_size, self.cartype)

	def getCarType(self):
		if self.cartype is None:
			self.cartype = rawdata.getCarType(self.raw_data)
			session.add(self)
			session.commit()
		return self.cartype

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

		# Check start and stop times
		t_start = dateutil.parser.parse(startTime)
		if t_start < first_timestamp or t_start > last_timestamp:
			raise StartTimeError
		t_stop = dateutil.parser.parse(stopTime)
		if t_stop < first_timestamp or t_stop > last_timestamp:
			raise StopTimeError

		# Check if cell_id exists
		cell_count = session.query(Packet.cell_id).filter(Packet.cell_id == cell_id).count()
		if cell_count == 0:
			raise CellIDError

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
			i += 1
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

timestamps = session.query(Packet.timestamp).order_by(Packet.timestamp).all()
first_timestamp = timestamps[0]
last_timestamp = timestamps[-1]


if __name__ == "__main__":
	pass
	#p = Packet(99, 99, 0, 1350555611626, 8, "rawdata2")
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
