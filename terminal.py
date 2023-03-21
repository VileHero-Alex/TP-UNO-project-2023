import random
import socket
import threading
from collections import deque
import json
import time

from errors import PopCardError, IllegalMove
from constants import *

from card import Card
from deck import PlayerDeck, TableDeck, DrawDeck
from server import Client, Server
from player import Player
from table import Table

class TerminalInterface(Player):
    def __init__(self, deque_lock: threading.Lock, *, conn=None, server=None, port=None, name=''):
        super().__init__(deque_lock, conn=conn, server=server, port=port, name=name)
        self.thread_listen = threading.Thread(self.listen_for_input)
        self.thread_update = threading.Thread(self.listen_for_updates)
        self.running = True
        # self.thread_listen.start()
        self.thread_update.start()

    def listen_for_input(self):
        while True:
            inp = input()
            if self.correct_play(inp):
                self.send()
            else:
                print("That's not the correct play")
    
    def card_to_human(self, card):
        pass
            

def host():
    server = Server(SERVER, port=5050)
    player = TerminalInterface(server.deque_lock, server=SERVER, port=PORT)
    inp = input("type \"start\" when all players are connected")
    while inp != input():
        inp = input()
    player.thread_listen.start()
    table = Table(server.clients.copy())

def join():
    lock = threading.Lock()
    player = TerminalInterface(lock, server=SERVER, port=PORT)
    player.thread_listen.start()


if __name__ == "__main__":
    inp = input("Would you like to host the game or join the game? (h/j)")
    while inp not in ['h', 'j']:
        inp = input("Nope, h or j")
    if inp == "h":
        host()
    join()