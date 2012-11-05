
import xml.etree.ElementTree as ET
import rawdata
import sql
from error import StartTimeError, StopTimeError, CellIDError, XMLError


NUM_CAR_TYPES = 12

class Request:
    
    def __init__(self, reqString):
        
        root = None
        self.error = None
        
        # Parse the string into an xml-tree
        try:
            root = ET.fromstring(reqString)
            self.id = root.tag
        except Exception:
            raise XMLError()
        
        # Retrieve relevant information
        try:
            self.type = root.find('RequestType').text
            if self.type != 'ListCells':
                self.startTime   = root.find('TimeStart').text
                self.stopTime    = root.find('TimeStop').text
                self.cellID      = root.find('CellID').text
        except Exception:
            pass # Error is handled in RequestHandler.process() instead, hoho..

    def process(self):
    
        try:
            if self.type == 'ListCells':
                xmlString = self.listCellsReply()
            elif self.type == 'CellStatSpeed':
                xmlString = self.cellStatSpeedReply()
            elif self.type == 'CellStatNet':
                xmlString = self.cellStatNetReply()
            else:
                raise XMLError(self.id)
            
            return xmlString
        
		except RequestError as e:
			return e.asXML(self.id)
				
	
	def listCellsReply(self):
		"""
		Lists all cells in the database in XML format
			
		<RequestType>ListCells</RequestType>
		<Cell>
			<CellID>CellID</CellID>
			(neighbors)
		</Cell>
		...
		"""
			
        # Retrieve all cells from the database as set
        cells = sql.Packet.listAllCells()
        # Convert to list and sort the elements
        cellList = list(cells)
        cellList.sort()
        
        # Generate xml with list of cells
        root = ET.Element(self.id)
        eType = ET.SubElement(root, 'RequestType')
        eType.text = self.type
        
        for cellID in cellList:
            print cellID
            eCell = ET.SubElement(root, 'Cell')
            eId = ET.SubElement(eCell, 'CellID')
            eId.text = str(cellID)
            # add neighbors?
                
        return ET.tostring(root)


    def cellStatSpeedReply(self):
		"""
		Calculates car speeds in a cell and outputs an XML string on the format:
			
		<RequestType>CellStatSpeed</RequestType>
		<Cell>
			<CellID>CellID</CellID>
			<TimeStart>StartTime</TimeStart>
			<TimeStop>StopTime</TimeStop>
			<DirectionCellIDA>
				<CarTypeA>
					<MinSpeed>3</Minspeed>
					<MaxSpeed>5</MaxSpeed>
					<AverageSpeed>4</AverageSpeed>
				</CarTypeA>
				<CarTypeB>
				...
			</DirectionCellIDA>
			<DirectionCellIDB>
				...
			</DirectionCellIDB>
		</Cell>
		"""
		
		# Create XML tree
        root = ET.Element(self.id)
        
        eType = ET.SubElement(root, 'RequestType')
        eType.text = self.type
        eCell = ET.SubElement(root, 'Cell')
        eId = ET.SubElement(eCell, 'CellID')
        eId.text = self.cellID
        eStart = ET.SubElement(eCell, 'TimeStart')
        eStart.text = self.startTime
        eStop = ET.SubElement(eCell, 'TimeStop')
        eStop.text = self.stopTime
        
		# Fetch packets from the database
        packets = sql.Packet.fetchInterval(self.cellID, self.startTime, self.stopTime)
        
		# Side of the road input-output mapping
        dirMap = { 0:'A', 1:'B' }

        for dirKey in dirMap:
			
            # One list per side of the road is generated
			eDir = ET.SubElement(eCell, 'DirectionCellID' + dirMap[dirKey])
			
            for carKey in range(1, NUM_CAR_TYPES + 1):
                relevantPackets = []
				
				# Sort packets by car type
                for p in packets:
                    if int(p.getCarType()) == carKey and int(p.road_side) == dirKey:
                        relevantPackets.append(p)
						packets.remove(p)
                
                eCar = ET.SubElement(eDir, 'CarType' + chr(65 + carKey))
                eMin = ET.SubElement(eCar, 'MinSpeed')
                eMax = ET.SubElement(eCar, 'MaxSpeed')
                eAvg = ET.SubElement(eCar, 'AverageSpeed')
                
                speeds = None
                    
				# Write packets to file, as required by process64
				# At least two packets are needed to calculate speeds
                if (len(relevantPackets) > 1):
                    path, filelist = sql.Packet.writeFiles(relevantPackets)
                    speeds = rawdata.getAvgSpeed(path, filelist)

                if speeds is not None:
                    min, max, avg = speeds
                    eMin.text = str(min)
                    eMax.text = str(max)
                    eAvg.text = str(avg)
                else:
					# If no speeds could be calculated, set all to 0
                    eMin.text = '0'
                    eMax.text = '0'
                    eAvg.text = '0'
        
        return ET.tostring(root)


    def cellStatNetReply(self):
		"""
		Calculates cell statistics and outputs an XML string on the format:
		
		<RequestType>CellStatNet</RequestType>
		<Cell>
			<CellID>CellID</CellID>
			<TimeStart>StartTime</TimeStart>
			<TimeStop>StopTime</TimeStop>
			<FirstCar>
				<CarType>C</CarType>
				<TimeStamp>201210051406</TimeStamp>
			</FirstCar>
			<LastCar>
				<CarType>A</CarType>
				<TimeStamp>201210051409</TimeStamp>
			</LastCar>
			<TotalCar>180000</TotalCar>
			<TotalAmountOfData>14560<TotalAmountOfData>
		</Cell>
		"""
		
        # Create xml-tree
        root = ET.Element(self.id)
        
        eType = ET.SubElement(root, 'RequestType')
        eType.text = self.type
        eCell = ET.SubElement(root, 'Cell')
        eId = ET.SubElement(eCell, 'CellID')
        eId.text = self.cellID
        eStart = ET.SubElement(eCell, 'TimeStart')
        eStart.text = self.startTime
        eStop = ET.SubElement(eCell, 'TimeStop')
        eStop.text = self.stopTime
        
        # Fetch all packets in the specified cell and time interval
        packets = sql.Packet.fetchInterval(self.cellID, self.startTime, self.stopTime)
        
        eFirst = ET.SubElement(eCell, 'FirstCar')
        eLast = ET.SubElement(eCell, 'LastCar')

        if len(packets) == 0:
            # Leave the fields empty if there are no cars in the db
            pass
        elif len(packets) == 1:
            # Only compute car type for one of the packets if firstCar == lastCar,
            # (this saves time if the car type is not already computed)
            carTypeInt = int(packets[0].getCarType())
            carType = chr(65 + carTypeInt)
            timeStamp = str(packets[0].getTimestamp())
            
            eCar = ET.SubElement(eFirst, 'CarType')
            eCar.text = carType
            eTime = ET.SubElement(eFirst, 'TimeStamp')
            eTime.text = timeStamp
            
            eCar = ET.SubElement(eLast, 'CarType')
            eCar.text = carType
            eTime = ET.SubElement(eLast, 'TimeStamp')
            eTime.text = timeStamp
            
        else:
            firstCarPacket = packets[0]
            lastCarPacket = packets[-1]
            
            eCar = ET.SubElement(eFirst, 'CarType')
            eCar.text = chr(65 + int(firstCarPacket.getCarType()))
            eTime = ET.SubElement(eFirst, 'TimeStamp')
            eTime.text = str(firstCarPacket.getTimestamp())
            
            eCar = ET.SubElement(eLast, 'CarType')
            eCar.text = chr(65 + int(lastCarPacket.getCarType()))
            eTime = ET.SubElement(eLast, 'TimeStamp')
            eTime.text = str(lastCarPacket.getTimestamp())
        
        eTotalCar = ET.SubElement(eCell, 'TotalCar')
        eTotalCar.text = str(len(packets))
        
		# Calculate total amount of raw data in the packets
        eTotalData = ET.SubElement(eCell, 'TotalAmountOfData')
        totData = 0
        for p in packets:
            totData += int(p.raw_data_size)
        eTotalData.text = str(totData / (1024 * 1024)) # size in MiB
        
        return ET.tostring(root)



