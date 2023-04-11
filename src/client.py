import threading
from collections import deque
import socket

import os
import configparser

config_file_path = os.path.join(os.path.dirname(__file__), '..', 'config.ini')
config = configparser.ConfigParser()
config.read(config_file_path)
HEADER = config.getint('SYSTEM CONFIG', 'HEADER')
FORMAT = config.get('SYSTEM CONFIG', 'FORMAT')
DISCONNECT_MESSAGE = config.get('SYSTEM CONFIG', 'DISCONNECT_MESSAGE')


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
            self.name = name
            print("[CLIENT STARTUP] client is connected to {}:{}".format(
                server, port))
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
        self.thread.join()

    def deque_append(self, msg):
        with self.deque_lock:
            self.deque.append(msg)

    def deque_popleft(self):
        try:
            with self.deque_lock:
                return self.deque.popleft()
        except IndexError:
            return None
