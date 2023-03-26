import socket
import threading
from src.player import Player


class Server():
    def __init__(self, server, port, deque_lock=None):
        self.server = server
        self.port = port
        if deque_lock:
            self.deque_lock = deque_lock
        else:
            self.deque_lock = threading.Lock()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.server, self.port))
        self.running = True
        self.clients = []
        self.socket.listen(1)
        self.thread = threading.Thread(target=self.wait_for_connections)
        self.thread.start()
        print("[SERVER STARTUP] server is running on {}:{}".format(self.server, self.port))
        
    def wait_for_connections(self):
        while self.running:
            conn, addr = self.socket.accept()
            self.clients.append(Player(self.deque_lock, conn=conn))
            print(f"[NEW CONNECTION] {self.clients[-1].name}: {addr} connected.")
            # print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 2}")