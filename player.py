from deck import PlayerDeck, TableDeck, DrawDeck
from server import Client
import json
import threading
import time

class Player(Client):
    def __init__(self, deque_lock: threading.Lock, *, conn=None, server=None, port=None, name=''):
        super().__init__()
        self.id = hash(name)
        self.deck = PlayerDeck()
        self.said_uno = False
        self.time_since_uno = time.time()

class Bot(Player):
    def update(self, info):
        self.status = json.loads(info)