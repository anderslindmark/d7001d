import socket
import threading
import SocketServer
import sql
from struct import unpack

class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    
    """A server class that starts a new thread for each request it handles."""
  
    def server_bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
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
        cell_id = int(self.bytes_to_int(cell_id))
        
        node_id = self.receive_bytes(4)
        node_id = int(self.bytes_to_int(node_id))
        
        road_side = ord(self.receive_bytes(1))
        
        timestamp = self.receive_bytes(8)
        timestamp = int(self.bytes_to_long(timestamp))
        
        size = self.receive_bytes(4)
        size = int(self.bytes_to_int(size))
        
        raw_data = self.receive_bytes(size)

        # Add the data to the database
        p = sql.Packet(cell_id, node_id, road_side, timestamp, size, raw_data)
        sql.session.add(p)
        sql.session.commit()
        
        self.request.close();
    
    def receive_bytes(self, size):
        """Receive exactly the specified number of bytes."""
        total_data = ""
        last_read = ""
        while True:
            last_read = self.request.recv(size)
            total_data += last_read
            size -= len(last_read)
            if size <= 0: break
        return total_data

    def bytes_to_int(self, byteArray):
        """Convert an array of 4 bytes to an unsigned integer."""
        result, = (unpack('>I', byteArray))
        return result

    def bytes_to_long(self, byteArray):
        """Convert an array of 8 bytes to an unsigned long long."""
        result, = (unpack('>Q', byteArray))
        return result


if __name__ == "__main__":
    PORT = 9999
    server = ThreadedTCPServer(('', PORT), SensorDataHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
    

