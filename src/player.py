import threading
from src.deck import PlayerDeck
from src.client import Client


class Player(Client):
    def __init__(self, deque_lock: threading.Lock, *, conn=None, server=None, port=None, name=''):
        super().__init__(deque_lock, conn=conn, server=server, port=port, name=name)
        self.id = hash(name)
        self.reinit()

    def reinit(self):
        self.deck = PlayerDeck()
        self.said_uno = False
        self.is_choosing = False
