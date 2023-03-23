from deck import PlayerDeck, TableDeck, DrawDeck
from server import Client
import json
import threading
import time

class Player(Client):
    def __init__(self, deque_lock: threading.Lock, *, conn=None, server=None, port=None, name=''):
        super().__init__(deque_lock, conn=conn, server=server, port=port, name=name)
        self.id = hash(name)
        self.reinit()
    
    def reinit(self):
        self.deck = PlayerDeck()
        self.said_uno = False
        self.is_choosing = False

class Bot(Player):
    def __init__(self, deque_lock: threading.Lock, *, conn=None, server=None, port=None, name=''):
        super().__init__(deque_lock, conn=conn, server=server, port=port, name=name)
    
    def __init__(self, deque_lock: threading.Lock, *, conn=None, server=None, port=None, name=''):
        super().__init__(deque_lock, conn=conn, server=server, port=port, name=name)
        self.thread_update = threading.Thread(target=self.update)
        self.running = True
        self.cards = []
        self.thread_update.start()
    
    def listen_for_updates(self):
        pass