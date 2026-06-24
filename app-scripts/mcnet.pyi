"""mcnet module stub/interface for fullmo MovingCap servo drives

The `mcnet` module provides a pyserial-style API for network socket communication for MovingCap CODE / Micropython on MovingCap. 

It allows creating TCP server, TCP client, UDP server and UDP client/peer sockets for easy implementation 
of custom application protocol layers, such as MODBUS TCP. 

Using an API similar to a serial communications API (instead of a Python socket/usocket library) provides extremely stable, safe and convenient communication functionality that offloads the actual script from concerns like socket binding, accepting or establishing connections, reconnect behavior, etc.

The module provides a class-based interface where you create McNet objects representing network connections.
Each McNet instance manages a socket connection and provides methods for reading and writing data.

Connection Settings Format:
    The settings string passed to McNet() defines the connection type and parameters:
    
    - TCP Server: "SERVER:port" or "SERVER:ip:port"
        Example: McNet("SERVER:10001") - TCP server on port 10001, any interface
        Example: McNet("SERVER:192.168.1.100:502") - TCP server on specific IP
    
    - TCP Client: "ip:port" or "hostname:port"
        Example: McNet("192.168.1.100:502") - Connect to TCP server at IP:port
        Example: McNet("plc.local:502") - Connect using hostname
    
    - UDP Server: "UDP:port" or "UDP:ip:port"
        Example: McNet("UDP:5000") - UDP server on port 5000
    
    - UDP Client/Peer: "UDP:ip:port"
        Example: McNet("UDP:192.168.1.100:5000") - UDP communication with remote host

Example Usage:
    # TCP Server example
    import mcnet
    server = mcnet.McNet("SERVER:10001")
    server.set_line_mode(1, ord("<"), ord(">"), 0, 0, 5000)
    while True:
        line = server.readline()
        if line:
            print("Received:", line)
            server.write("OK\\n")
    
    # TCP Client example
    client = mcnet.McNet("192.168.1.100:502")
    if client.is_connected():
        client.write(b"\\x00\\x01\\x00\\x00\\x00\\x06")  # MODBUS request
        response = client.read(256)
        print("Response:", response)
    client.close()
"""
__author__ =  "Oliver Heggelbacher"
__email__ = "oliver.heggelbacher@fullmo.de"
__version__ = "50.00.08.xx"
__date__ = "2025-02-03"

class McNet:
    """Network socket communication class with pyserial-like API.
    
    This class represents a network socket connection (TCP or UDP, client or server).
    It provides a simple, serial-port-like interface for network communication.
    """
    
    def __init__(self, settings: str):
        """Create and open a new network connection.
        
        :param settings: Connection settings string specifying the socket type and parameters.
            Format depends on connection type (see module documentation).
        :type settings: str
        :raises OSError: If socket cannot be opened (e.g., all sockets in use, invalid settings)
        
        Example:
            server = McNet("SERVER:10001")  # TCP server
            client = McNet("192.168.1.100:502")  # TCP client
        """
        pass
    
    def open(self, settings: str) -> bool:
        """Open a network connection (or reopen after close).
        
        :param settings: Connection settings string (see __init__)
        :type settings: str
        :return: True if successful, False if failed.
        :rtype: bool
        """
        pass
    
    def is_open(self) -> bool:
        """Check if the socket is open.
        
        Returns True if the socket has been opened (even if not yet connected).
        For TCP clients, this indicates the socket exists but may still be connecting.
        For TCP servers, this indicates the server socket is listening.
        
        :return: True if socket is open, False otherwise.
        :rtype: bool
        """
        pass
    
    def is_connected(self) -> bool:
        """Check if the connection is established and ready for data transfer.
        
        For TCP clients: Returns True when connection to server is established.
        For TCP servers: Returns True when a client is connected.
        For UDP: Usually returns True if socket is open (UDP is connectionless).
        
        :return: True if connected, False otherwise.
        :rtype: bool
        """
        pass
    
    def close(self):
        """Close the network connection and release the socket.
        
        This cleanly shuts down the connection and frees the socket resource
        for reuse by other McNet instances.
        """
        pass
    
    def write(self, data) -> int:
        """Write data to the network connection.
        
        Accepts both string and bytes-like objects. Strings are automatically
        encoded as UTF-8. The data is sent over the network connection.
        
        :param data: Data to send. Can be str, bytes, bytearray, or memoryview.
        :type data: str or bytes-like
        :return: Number of bytes written, or negative value on error.
        :rtype: int
        
        Example:
            s.write("Hello\\n")  # Send string
            s.write(b"\\x01\\x02\\x03")  # Send bytes
        """
        pass
    
    def read(self, size: int = 0):
        """Read available data from the network connection.
        
        Reads up to 'size' bytes from the receive buffer. If size is 0 or omitted,
        reads all available data. Returns None if no data is available.
        
        The return type depends on the text_mode setting:
        - If text_mode is True: returns str
        - If text_mode is False: returns bytes
        
        :param size: Maximum number of bytes to read. 0 = read all available.
        :type size: int
        :return: Data read as str or bytes, or None if no data available.
        :rtype: str or bytes or None
        
        Example:
            data = s.read()  # Read all available
            data = s.read(100)  # Read up to 100 bytes
        """
        pass
    
    def readline(self):
        """Read a line of data based on line mode configuration.
        
        This method uses the line parsing parameters configured with set_line_mode().
        It waits for and extracts a complete line based on the start/end markers
        and timeout settings.

        The answer includes the start and end markers, if specified.  
        
        Returns None if no complete line is available or timeout expires.
        
        :return: Line data as str or bytes (depending on text_mode), or None. 
        :rtype: str or bytes or None
        
        Example:
            s.set_line_mode(1, ord('<'), ord('>'), 0, 0, 5000)
            line = s.readline()  # Reads data between '<' and '>'
        """
        pass
    
    def read_until(self, expected: str = "\\n", size: int = 0):
        """Read data until a specific sequence is found.
        
        Reads from the connection until the expected byte sequence is encountered,
        or until 'size' bytes have been read (if size > 0), or until no more data
        is available.
        
        The expected sequence is included in the returned data.
        
        :param expected: Byte sequence to read until. Can be str or bytes. Default is newline.
        :type expected: str or bytes
        :param size: Maximum bytes to read (0 = no limit).
        :type size: int
        :return: Data read as str or bytes (depending on text_mode), or None.
        :rtype: str or bytes or None
        
        Example:
            data = s.read_until("\\r\\n")  # Read until CRLF
            data = s.read_until(b"\\x00", 1024)  # Read until null byte, max 1024 bytes
        """
        pass
    
    def set_line_mode(self, text_mode: int, start_marker: int, end_marker: int, min_len: int, max_len: int, timeout: int) -> int:
        """Configure line parsing mode for readline() method.
        
        This configures how readline() extracts lines from the data stream.
        The start and end markers define the line boundaries, min_len and max_len
        provide additional constraints to disambiguate protocols where data may
        contain marker bytes, and timeout specifies how long to wait for a complete line.
        
        For binary protocols where data payloads may contain bytes matching the start
        or end markers, use min_len and max_len to specify exact or constrained frame sizes.
        For example, a fixed-length binary protocol frame can use min_len = max_len = frame_size.
        
        :param text_mode: If > 0, return data as str (text mode). If 0, return as bytes.
        :type text_mode: int
        :param start_marker: ASCII code of line start marker character (e.g., ord('<') = 60), or 0 for no start marker.
        :type start_marker: int
        :param end_marker: ASCII code of line end marker character (e.g., ord('>') = 62), or 0 for no end marker.
        :type end_marker: int
        :param min_len: Minimum line/frame length in bytes (including markers), or 0 for no minimum.
            Used to skip ambiguous end markers that appear before this position.
        :type min_len: int
        :param max_len: Maximum line/frame length in bytes (including markers), or 0 for no maximum.
            Limits the search range for the end marker.
        :type max_len: int
        :param timeout: Timeout in milliseconds to wait for complete line (max 60000), or 0 for no timeout.
        :type timeout: int
        :return: 0 on success, negative on error.
        :rtype: int
        
        Example:
            # Text protocol with angle brackets
            s.set_line_mode(1, ord('<'), ord('>'), 0, 0, 5000)
            
            # Binary protocol: fixed 9-byte frames with STX/ETX markers
            # [STX][CMD][LEN][DATA(4)][CHECKSUM][ETX] where data may contain 0x02 or 0x03
            s.set_line_mode(0, 0x02, 0x03, 9, 9, 1000)
            
            # Variable-length protocol: frames between 5 and 260 bytes
            s.set_line_mode(0, 0x02, 0x03, 5, 260, 500)
        """
        pass
    
    def in_waiting(self) -> int:
        """Get the number of bytes available in the receive buffer.
        
        Returns the count of bytes that can be read immediately without blocking.
        Useful for checking if data is available before calling read().
        
        :return: Number of bytes available to read, or negative value on error.
        :rtype: int
        
        Example:
            if s.in_waiting() > 0:
                data = s.read()
        """
        pass
    
    def reset_input_buffer(self):
        """Clear the input receive buffer.
        
        Discards all data currently in the receive buffer. Useful for
        resynchronizing communication or clearing stale data.
        
        Example:
            s.reset_input_buffer()  # Clear any pending data
            s.write("NEW_REQUEST")
        """
        pass