from big_fucking_file import *

'''import random
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
from table import Table'''

class TerminalInterface(Client):
    def __init__(self, deque_lock: threading.Lock, *, conn=None, server=None, port=None, name=''):
        super().__init__(deque_lock, conn=conn, server=server, port=port, name=name)
        self.thread_listen = threading.Thread(target=self.listen_for_input)
        self.thread_update = threading.Thread(target=self.listen_for_updates)
        self.running = True
        self.cards = []
        # self.thread_listen.start()
        self.thread_update.start()
    
    def listen_for_updates(self):
        while True:
            event = self.deque_popleft()
            while event:
                self.print_update(event)
                event = self.deque_popleft()

    def print_update(self, event):
        event = json.loads(event)
        print("------------------------------------------")
        if not event["ok"]:
            print(event["error"])
            return
        if event["status"] == "finished":
            print(f"Player {event['winnner']['name']} won!")
            return
        
        for player in event["info"]["players"]:
            print(f"{player['turn_id'] + 1}. {player['name']}: {player['cards_amount']} cards")
        card_id = event['info']['top_card_id']
        color = event['info']['top_card_color']
        print(f"Last played card: {color}_{Card(card_id).type}")

        turn = event['info']['turn']
        if turn == "you":
            print("It's your turn.", end=" ")
        else:
            print(f"It's {event['info']['players'][turn]['name']}\'s turn.", end='')
        if event['info']['is_direction_clockwise']:
            print("The direction is clockwise")
        else:
            print("The direction is COUNTERclockwise")
        print()
        print("Your cards:")
        self.cards = event['info']['my_cards']
        self.cards.sort()
        for card in self.cards[:-6]:
            print(self.card_to_human(card), end=', ')
        print()


    def listen_for_input(self):
        while True:
            inp = input()
            if self.correct_play(inp):
                pool = self.human_to_card(inp)
                for card in self.cards:
                    if card in pool:
                        print(card)
                        self.send(str(card))
                        break
            else:
                print("That's not the correct play")
    
    def card_to_human(self, card_id) -> str:
        card = Card(card_id)
        if card.type in Card.type_pool_extra:
            return card.type
        s = card.color + "_" + card.type
        return s
        
    
    def human_to_card(self, inp) -> list:
        if inp in Card.type_pool_extra:
            return [Card.type_pool_extra.index(inp) + 108]
        if inp.count("_") != 1:
            return None
        color, type = inp.split("_")
        if color not in Card.color_pool or type not in Card.type_pool:
            return None
        if type == "choose":
            return [100, 101, 102, 103]
        if type == "+4":
            return [104, 105, 106, 107]
        id = Card.color_pool.index(color) * 25
        if type == '0':
            return [id]
        id += Card.type_pool.index(type) * 2
        return [id - 1, id]
    
    def correct_play(self, inp):
        pool = self.human_to_card(inp)
        if not pool:
            return False
        return any([id in self.cards for id in pool])
        

            

def host(name):
    server = Server(SERVER, port=5050)
    player = TerminalInterface(server.deque_lock, server=SERVER, port=PORT, name=name)
    '''inp = input("type \"start\" when all players are connected\n")
    while inp != "start":
        inp = input()'''
    player.thread_listen.start()
    table = Table(server.clients.copy())

def join(name):
    lock = threading.Lock()
    player = TerminalInterface(lock, server=SERVER, port=PORT, name=name)
    player.thread_listen.start()


if __name__ == "__main__":
    join("PLAYER 2")