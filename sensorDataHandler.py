import socket
import threading
import SocketServer
import sql
import logging
import os
import errno

from struct import unpack

class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    """A server class that starts a new thread for each request it handles."""
  
    def server_bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Set timeout in seconds
        self.socket.settimeout(10)
        self.socket.bind(self.server_address)


class SensorDataHandler(SocketServer.BaseRequestHandler):
    """
    Request handler that receives data from the sensor network and
    stores it in our database.
    """

    def handle(self):
        """Handle incoming TCP traffic."""
        
        # Read data from the network
        cell_id = self.receive_bytes(4)
        node_id = self.receive_bytes(4)
        road_side = self.receive_bytes(1)
        timestamp = self.receive_bytes(8)
        size = self.receive_bytes(4)
        
        # Convert the data to the right format
        try:
            cell_id = int(bytes_to_int(cell_id))
            node_id = int(bytes_to_int(node_id))
            road_side = ord(road_side)
            timestamp = int(bytes_to_long(timestamp))
            size = int(bytes_to_int(size))
        except:
            print "Faulty data format"
            logging.exception("Faulty data format.");
            self.request.close()
            return

        f = open('NickesTestFile', 'w')
        f.write("Hello!)
        f.close()
        
        # Add the data to the database
        p = sql.Packet(cell_id, node_id, road_side, timestamp, size, raw_data)
        
        print "Data successfully stored on the database, probably."
        self.request.close()
    
    def receive_bytes(self, size):
        """Receive exactly the specified number of bytes."""
        total_data = ""
        last_read = ""
        while True:
            
            try:
                last_read = self.request.recv(size)
            except:
                print "Error receiving message"
                logging.exception("Error receiving message");
                return None
            
            total_data += last_read
            size -= len(last_read)
            if size <= 0: break
        return total_data


def bytes_to_int(byteArray):
    """Convert an array of 4 bytes to an unsigned integer."""
    result, = (unpack('>I', byteArray))
    return result


def bytes_to_long(byteArray):
    """Convert an array of 8 bytes to an unsigned long long."""
    result, = (unpack('>Q', byteArray))
    return result

    
def make_sure_path_exists(path):
    """
    Creates the given folder if it doesn't already exist,
    in a tread-safe manner
    """
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise


if __name__ == "__main__":

    make_sure_path_exists('/home/ubuntu/logs/')
    logging.basicConfig(filename='/home/ubuntu/logs/sensorDataHandler.log', level=logging.DEBUG)

    PORT = 9999
    server = ThreadedTCPServer(('', PORT), SensorDataHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
