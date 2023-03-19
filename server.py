import socket
import threading
import time
from constants import *
from collections import deque

class Client:
    def __init__(self, deque_lock: threading.Lock, *, conn=None, server=None, port=None, name=''):
        self.deque_lock = deque_lock
        self.deque = deque()
        if conn:
            self.conn = conn
            self.name = self.receive()
        else:
            self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.conn.connect((server, port))
            self.send(name)
            print("[CLIENT STARTUP] client is connected to {}:{}".format(server, port))
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
                self.deque_append(msg)
        self.conn.close()
    
    def deque_append(self, msg):
        with self.deque_lock:
            self.deque.append(msg)
    
    def deque_popleft(self):
        with self.deque_lock:
            return self.deque.popleft()

class ClientFromSocket(Client):
    def __init__(self, conn: socket.socket):
        self.conn = conn
        self.name = self.receive()
        super().__init__()

class ClientFromAddress(Client):
    def __init__(self, server: str, port: str, name=''):
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn.connect((server, port))
        self.send(name)
        print("[CLIENT STARTUP] client is connected to {}:{}".format(server, port))
        super().__init__()


class Server():
    def __init__(self, deque_lock, server, port):
        self.server = server
        self.port = 5050
        self.deque_lock = deque_lock
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        while True:
            try:
                self.socket.bind((self.server, self.port))
                break
            except OSError:
                self.port += 1
        self.clients = []
        self.socket.listen(1)
        self.thread = threading.Thread(target=self.wait_for_connections)
        self.thread.start()
        print("[SERVER STARTUP] server is running on {}:{}".format(self.server, self.port))
        
    def wait_for_connections(self):
        while True:
            conn, addr = self.socket.accept()
            self.clients.append(Client(self.deque_lock, conn=conn))
            print(f"[NEW CONNECTION] {addr} connected.")
            print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 3}")


if __name__ == '__main__':
    deque_lock = threading.Lock()
    port = 5050

    server = Server(deque_lock, SERVER, port)
    port = server.port
    
    while True:
        for client in server.clients:
            while len(client.deque) > 0:
                message = client.deque_popleft()
                print(client.name, ": ", message, sep='')