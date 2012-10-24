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
	"""
	This class contains the database mapping for a 'packet' from the sensor data group 
	and helper methods for dealing with that data.
	"""
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
		"""
		Create a packet, if commit is true (default) then the packet is added to the database automatically
		"""
		global session

		self.cell_id = cell_id
		self.node_id = node_id
		self.road_side = road_side
		# Timestamp is in ms since epoch.
		t = datetime.fromtimestamp(timestamp/1000)
		self.timestamp = t.strftime("%Y-%m-%d %H:%M:%S")
		self.raw_data_size = raw_data_size
		self.raw_data = raw_data
		self.cartype = None

		if commit:
			# Commit right away so that p.id is available and can be placed onto queue
			session.add(self)
			session.commit()
			enQueue(self.id)


	def __repr__(self):
		return "<Packet('%d', '%d', '%s', '*DATA*', '%s', '%s')>" % (self.cell_id, self.node_id, self.timestamp, self.raw_data_size, self.cartype)

	def getCarType(self):
		"""
		Returns the cartype. If cartype has not yet been calculated it will be done, which can take a while.
		"""
		global session
		if self.cartype is None:
			cartype = rawdata.getCarType(self.raw_data)
			if cartype is None:
				# Delete packet from db
				print "Corrupt packet, deleting from DB"
				session.delete(self)
				return None
			else:
				self.cartype = cartype
				session.add(self)
				session.commit()
		return self.cartype

	def getTimestamp(self):
		"""
		Return the timestamp in an XML-friendly fashion.
		"""
		return self.timestamp.strftime("%Y%m%d%H%M")

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
		"""
		Return all packets in cell cell_id between startTime and stopTime.
		Will raise startTime or stopTime are malformed it will raise StartTimeError or StopTimeError
		If startTime is after stopTime it will raise StartTimeError
		If there is not a cell with the specified cell_id it will raise CellIDError
		"""
		global session

		try:
			startTime = Packet._fixTimes(startTime)
		except:
			raise StartTimeError()
		try:
			stopTime = Packet._fixTimes(stopTime)
		except:
			raise StopTimeError()

		# Check start and stop times
		t_start = dateutil.parser.parse(startTime)
		t_stop = dateutil.parser.parse(stopTime)
		if t_start > t_stop:
			raise StartTimeError()

		# Check if cell_id exists
		cell_count = session.query(Packet.cell_id).filter(Packet.cell_id == cell_id).count()
		if cell_count == 0:
			raise CellIDError()

		l = []
		for packet in session.query(Packet).filter(and_(Packet.cell_id == cell_id, Packet.timestamp.between(startTime, stopTime))).order_by(Packet.timestamp):
			l.append(packet)
		return l

	@staticmethod
	def writeFiles(packets):
		"""
		Takes a list of packets and writes the data from each packet to a file.
		Returns a tuple consisting of the directory containing the files and a list of filenames.
		"""
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
		"""
		Returns a set with all cell_id's.
		"""
		global session
		ids = set()
		result = session.query(Packet.cell_id).all()
		for row in result:
			ids.add(row.cell_id)
		return ids

# To create the table; first drop existing table using:
#    Packet.metadata.drop_all(engine)
# and and then create it with:
#    Packet.metadata.create_all(engine)

def wipeDatabase():
	"""
	Removes all packets from the database, drops the database table and then creates the table again.
	"""
	plist = session.query(Packet).all()
	for packet in plist:
		session.delete(packet)
	session.commit()
	Packet.metadata.drop_all(engine)
	Packet.metadata.create_all(engine)

# String used for connecting to the database
ENGINE_STRING = "mysql://" + aws_common.DB_USER + ':' + aws_common.DB_PASSWORD + '@' + aws_common.DB_ADDRESS + '/' + aws_common.DB_DATABASE

# SQLAlchemy engine and session
engine = create_engine(ENGINE_STRING, echo=DB_DEBUG)
Session = sessionmaker(bind=engine)
session = Session()

if __name__ == "__main__":
	pass
	#p = Packet(99, 99, 0, 1350555611626, 8, "rawdata2")
	
	# Incoming packets from the Sensor Network
	#  import sql
	#  cell_id, node_id, road_side, timestamp, size, rawdata = recievePacket()
	#  p = sql.Packet(cell_id, node_id, road_side, timestamp, size, rawdata)
	# Done.

	# Requests from the front-end
	#  from sql import Packet
	#  import rawdata
	#  import S3
	#  packets = Packet.fetchInterval(startTime, stopTime)
	#  path, files = Packet.writeFiles(packets)
	#  min, max, avgSpeed = rawdata.getAvgSpeed(path, files)
	# Get XML strings etc
	#  url = S3.uploadFile(filnamn, xmltext)
	# Done.
