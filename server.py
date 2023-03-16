import socket
import threading
import time
from constants import *
from collections import deque

class Client:
    def __init__(self):
        self.deque = deque()
        self.thread = threading.Thread(target=self.wait_for_messages)
        self.thread.start()
        
    def send(self, data):
        message = data.encode(FORMAT)
        msg_length = len(message)
        send_length = str(msg_length).encode(FORMAT)
        send_length += b' ' * (HEADER - len(send_length))
        try:
            self.conn.send(send_length)
            self.conn.send(message)
        except BrokenPipeError or ConnectionAbortedError or ConnectionResetError or InterruptedError:
            self.send(self, data)
        
    def receive(self):
        msg_length = self.conn.recv(HEADER).decode(FORMAT)
        if msg_length:
            msg_length = int(msg_length)
            msg = self.conn.recv(msg_length).decode(FORMAT)
            return msg
        return None
    
    def wait_for_messages(self):
        connected = True
        while connected:
            try:
                msg = self.receive()
            except ConnectionError:
                connected = False
                break
            if msg:
                if msg == DISCONNECT_MESSAGE:
                    connected = False
                self.deque.append(msg)
        self.conn.close()

class ClientFromSocket(Client):
    def __init__(self, conn: socket.socket):
        self.conn = conn
        self.name = self.receive()
        super().__init__()

class ClientFromAddress(Client):
    def __init__(self, host: str, port: str, name=''):
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn.connect((host, port))
        self.send(name)
        print("[CLIENT STARTUP] client is connected to {}:{}".format(host, port))
        super().__init__()


class Server():
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        while True:
            try:
                self.socket.bind((self.host, self.port))
                break
            except OSError:
                self.port += 1
        self.clients = []
        self.socket.listen(1)
        self.thread = threading.Thread(target=self.wait_for_connections)
        self.thread.start()
        print("[SERVER STARTUP] server is running on {}:{}".format(self.host, self.port))
        
    def wait_for_connections(self):
        while True:
            conn, addr = self.socket.accept()
            self.clients.append(ClientFromSocket(conn))
            print(f"[NEW CONNECTION] {addr} connected.")
            print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 3}")


if __name__ == '__main__':
    port = 5050

    server = Server(SERVER, port)
    port = server.port
    
    while True:
        for client in server.clients:
            while len(client.deque) > 0:
                message = client.deque.popleft()
                print(client.name, ": ", message, sep='')