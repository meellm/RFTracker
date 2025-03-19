import socket
import logging

class Bluetooth:
    def __init__(self, bluetooth_port, server_address):
        self.server_socket = None
        self.client_socket = None
        self.client_address = None
        self.connection_flag = False
        self.server_address = server_address
        self.bluetooth_port = bluetooth_port

        self.whatAmI = None

        self.logger = logging.getLogger(__name__)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def send_data(self, data):
        if not self.client_socket:
            self.logger.warning("No connection to send data")
            return False

        try:
            self.client_socket.send((str(data)).encode("utf-8"))
            return True
        except socket.error as e:
            self.logger.error(f"Failed to send data: {e}")
            if self.whatAmI == "server":
                self.start_server()
            elif self.whatAmI == "client":
                self.connect_server()
            return False

    def receive_data(self):
        if not self.client_socket:
            self.logger.warning("No connection to receive data")
            return None

        try:
            data = self.client_socket.recv(1024).decode("utf-8")
            return data
        except socket.error as e:
            self.logger.error(f"Failed to receive data: {e}")
            if self.whatAmI == "server":
                self.start_server()
            elif self.whatAmI == "client":
                self.connect_server()
            return None

    def check_connection(self):
        if not self.client_socket:
            return False

        try:
            self.client_socket.getpeername()
            self.connection_flag = True
        except (socket.error, OSError):
            self.client_socket = None
            self.client_address = None
            self.connection_flag = False

        return self.connection_flag

    def start_server(self):
        try:
            self.close_server()

            self.server_socket = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
            self.server_socket.bind((self.server_address, self.bluetooth_port))
            self.server_socket.listen(1)

            self.logger.info("SERVER ON. Waiting for connection...")
            self.client_socket, self.client_address = self.server_socket.accept()
            self.logger.info(f"Connection established with: {self.client_address}")

            self.connection_flag = True
            self.whatAmI = "server"

            return True
        except socket.error as e:
            self.logger.error(f"Failed to start server: {e}")
            self.client_address = None
            self.client_socket = None
            self.connection_flag = False

            return False

    def close_server(self):
        if self.client_socket is not None:
            try:
                self.client_socket.close()
                self.logger.debug("Client socket closed")
            except socket.error as e:
                self.logger.error(f"Failed to close client socket: {e}")

        if self.server_socket is not None:
            try:
                self.server_socket.close()
                self.logger.debug("Server socket closed")
            except socket.error as e:
                self.logger.error(f"Failed to close server socket: {e}")

        self.whatAmI = None
        self.client_socket = None
        self.client_address = None
        self.connection_flag = False
        self.logger.info("Bluetooth server closed")

    def connect_server(self):
        try:
            self.client_socket = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
            self.client_socket.connect((self.server_address, self.bluetooth_port))
            self.logger.info("Connection to Bluetooth server established")
            self.connection_flag = True
            self.whatAmI = "client"
            return True
        except socket.error as e:
            self.logger.error(f"Failed to connect to server: {e}")
            self.client_socket = None
            self.connection_flag = False
            return False

    def disconnect_server(self):
        if not self.client_socket:
            return True

        try:
            self.client_socket.close()
            self.client_socket = None
            self.logger.info("Disconnected from Bluetooth server")
            self.connection_flag = False
            return True
        except socket.error as e:
            self.logger.error(f"Failed to disconnect from server: {e}")
            return False

    def wait_client(self):
        if self.client_socket:
            return True

        try:
            if self.server_socket:
                self.client_socket, self.client_address = self.server_socket.accept()
                self.logger.info(f"Connection established with: {self.client_address}")
                self.connection_flag = True
                return True
            else:
                self.logger.warning("Server socket not initialized")
                return False
        except socket.error as e:
            self.logger.error(f"Failed to accept client connection: {e}")
            self.client_socket = None
            self.client_address = None
            self.connection_flag = False
            return False
