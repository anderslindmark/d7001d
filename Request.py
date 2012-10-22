
import xml.etree.ElementTree as ET

import rawdata
import sql
import error

class Request:
    
    def __init__(self, reqString):
        
        root = None
        self.error = None
        
        try:
            root = ET.fromstring(reqString)
            self.id = root.tag
        except Exception:
            self.id = ''
            #raise XMLError()
        
        try:
            self.type = root.find('RequestType').text
            if self.type != 'ListCells':
                self.startTime   = root.find('TimeStart').text
                self.stopTime    = root.find('TimeStop').text
                self.cellID      = root.find('CellID').text
        except Exception:
            pass # Error is handled in process() instead, hoho..
            #raise XMLError(self.id)
    

    def process(self):
    
        try:
            if self.type == 'ListCells':
                xmlString = self.listCellsReply()
            elif self.type == 'CellStatSpeed':
                xmlString = self.cellStatSpeedReply()
            elif self.type == 'CellStatNet':
                xmlString = self.cellStatNetReply()
            else:
                raise error.XMLError(self.id)
            
            return xmlString
        
        except error.StartTimeError:
            return self.fakeStartTimeError()
        except error.StopTimeError:
            return self.fakeStopTimeError()
        except error.CellIDError:
            return self.fakeCellIDError()
        except error.XMLError:
            return self.fakeXMLError()
        except Exception as e:
            # Return xml-error for any other error :)
            return str(e) #self.fakeXMLError()
        except:
            return 'RUH-ROH!'
                
    def fakeXMLError(self):
        return """
<""" + self.id + """>
    <Error>
        <XMLError>
        <ErrorDescription>Error in XML syntax</ErrorDescription>
        </XMLError>
    </Error>
</""" + self.id + ">"

    def fakeStartTimeError(self):
        return """
<""" + self.id + """>
    <Error>
        <StartTimeError>
            <ErrorData>""" + self.startTime + """</ErrorData>
            <ErrorDescription>Out of range</ErrorDescription>
        </StartTimeError>
    </Error>
</""" + self.id+  ">"

    def fakeStopTimeError(self):
        return """
<""" + self.id + """>
    <Error>
        <StopTimeError>
            <ErrorData>""" + self.stopTime + """</ErrorData>
            <ErrorDescription>Out of range</ErrorDescription>
        </StopTimeError>
    </Error>
</""" + self.id + ">"

    def fakeCellIDError(self):
        return """
<""" + self.id + """>
    <Error>
        <CellIDError>
            <ErrorData>""" + self.cellID + """</ErrorData>
                <ErrorDescription>No such cell</ErrorDescription>
        </CellIDError>
    </Error>
</""" + self.id + ">"


    def listCellsReply(self):
        
        cells = sql.Packet.listAllCells() # all cells as set
        cellList = list(cells)
        cellList.sort()
        
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
        
        packets = sql.Packet.fetchInterval(self.cellID, self.startTime, self.stopTime)
        
        dirMap = { 0:'A', 1:'B' }
        carMap = { 1:'A', 2:'B', 3:'C', 4:'D', 5:'E', 6:'F' }
        
        for dirKey in dirMap:
            eDir = ET.SubElement(eCell, 'DirectionCellID' + dirMap[dirKey])
            for carKey in carMap:
                relevantPackets = []
                for p in packets:
                    if int(p.getCarType()) == carKey and int(p.road_side) == dirKey:
                        relevantPackets.append(p)
                
                eCar = ET.SubElement(eDir, 'CarType' + carMap[carKey])
                eMin = ET.SubElement(eCar, 'MinSpeed')
                eMax = ET.SubElement(eCar, 'MaxSpeed')
                eAvg = ET.SubElement(eCar, 'AverageSpeed')
                
                if (len(relevantPackets) > 1):
                    path, filelist = sql.Packet.writeFiles(relevantPackets)
                    min, max, avg = rawdata.getAvgSpeed(path, filelist)
                    eMin.text = str(min)
                    eMax.text = str(max)
                    eAvg.text = str(avg)
                else:
                    eMin.text = '0'
                    eMax.text = '0'
                    eAvg.text = '0'
        
        return ET.tostring(root)

#    return """
#    <RequestType>CellStatSpeed</RequestType>
#    <Cell>
#        <CellID>""" + req.cellID + """</CellID>
#        <TimeStart>""" + req.startTime + """</TimeStart>
#        <TimeStop>""" + req.stopTime + """</TimeStop>
#        <DirectionCellIDA>
#            <CarTypeA>
#                <MinSpeed>3</Minspeed>
#                <MaxSpeed>5</MaxSpeed>
#                <AverageSpeed>4</AverageSpeed>
#            </CarTypeA>
#            <CarTypeB>
#                <MinSpeed>0</Minspeed>
#                <MaxSpeed>6</MaxSpeed>
#                <AverageSpeed>1</AverageSpeed>
#            </CarTypeB>
#            <CarTypeC>
#                <MinSpeed>3</Minspeed>
#                <MaxSpeed>5</MaxSpeed>
#                <AverageSpeed>4</AverageSpeed>
#            </CarTypeC>
#            <CarTypeD>
#                <MinSpeed>3</Minspeed>
#                <MaxSpeed>5</MaxSpeed>
#                <AverageSpeed>4</AverageSpeed>
#            </CarTypeD>
#            <CarTypeE>
#                <MinSpeed>3</Minspeed>
#                <MaxSpeed>5</MaxSpeed>
#                <AverageSpeed>4</AverageSpeed>
#            </CarTypeE>
#            <CarTypeF>
#                <MinSpeed>3</Minspeed>
#                <MaxSpeed>5</MaxSpeed>
#                <AverageSpeed>4</AverageSpeed>
#            </CarTypeF>
#        </DirectionCellIDA>
#        <DirectionCellIDB>
#            <CarTypeA>
#                <MinSpeed>3</Minspeed>
#                <MaxSpeed>5</MaxSpeed>
#                <AverageSpeed>4</AverageSpeed>
#            </CarTypeA>
#            <CarTypeB>
#                <MinSpeed>3</Minspeed>
#                <MaxSpeed>5</MaxSpeed>
#                <AverageSpeed>4</AverageSpeed>
#            </CarTypeB>
#            <CarTypeC>
#                <MinSpeed>3</Minspeed>
#                <MaxSpeed>5</MaxSpeed>
#                <AverageSpeed>4</AverageSpeed>
#            </CarTypeC>
#            <CarTypeD>
#                <MinSpeed>3</Minspeed>
#                <MaxSpeed>5</MaxSpeed>
#                <AverageSpeed>4</AverageSpeed>
#            </CarTypeD>
#            <CarTypeE>
#                <MinSpeed>3</Minspeed>
#                <MaxSpeed>5</MaxSpeed>
#                <AverageSpeed>4</AverageSpeed>
#            </CarTypeE>
#            <CarTypeF>
#                <MinSpeed>3</Minspeed>
#                <MaxSpeed>5</MaxSpeed>
#                <AverageSpeed>4</AverageSpeed>
#            </CarTypeF>
#        </DirectionCellIDB>
#    </Cell>
#"""


    def cellStatNetReply(self):
        
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
        
        packets = sql.Packet.fetchInterval(self.cellID, self.startTime, self.stopTime)
        
        eFirst = ET.SubElement(eCell, 'FirstCar')
        eLast = ET.SubElement(eCell, 'LastCar')
        
        # map(chr, range(65, 65 + numCarTypes)) -> ['A', 'B', 'C', ...]
        carMap = { 1:'A', 2:'B', 3:'C', 4:'D', 5:'E', 6:'F' }
        
        if len(packets) == 0:
            # Leave the fields empty if there are no cars in the db
            pass
        elif len(packets) == 1:
            # Only compute car type once if firstCar == lastCar,
            # (this saves time if the car type is not already computed)
            carType = carMap[int(packets[0].getCarType())]
            timeStamp = str(packets[0].timestamp)
            
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
            lastCarPacket = packets[len(packets) - 1]
            
            eCar = ET.SubElement(eFirst, 'CarType')
            eCar.text = carMap[int(firstCarPacket.getCarType())]
            eTime = ET.SubElement(eFirst, 'TimeStamp')
            eTime.text = str(firstCarPacket.timestamp)
            
            eCar = ET.SubElement(eLast, 'CarType')
            eCar.text = carMap[int(lastCarPacket.getCarType())]
            eTime = ET.SubElement(eLast, 'TimeStamp')
            eTime.text = str(lastCarPacket.timestamp)
        
        eTotalCar = ET.SubElement(eCell, 'TotalCar')
        eTotalCar.text = str(len(packets))
        
        eTotalData = ET.SubElement(eCell, 'TotalAmountOfData')
        totData = 0
        for p in packets:
            totData += int(p.raw_data_size)
        eTotalData.text = str(totData / (1024 * 1024)) # size in MiB
        
        return ET.tostring(root)

#    return """
#    <RequestType>CellStatNet</RequestType>
#    <Cell>
#        <CellID>""" + req.cellID + """</CellID>
#        <TimeStart>""" + req.startTime + """</TimeStart>
#        <TimeStop>""" + req.stopTime + """</TimeStop>
#        <FirstCar>
#            <CarType>C</CarType>
#            <TimeStamp>201210051406</TimeStamp>
#        </FirstCar>
#        <LastCar>
#            <CarType>A</CarType>
#            <TimeStamp>201210051409</TimeStamp>
#        </LastCar>
#        <TotalCar>180000</TotalCar>
#        <TotalAmountOfData>14560<TotalAmountOfData>
#    </Cell>
#"""



