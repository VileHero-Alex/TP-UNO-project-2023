import threading
import json

from src.client import Client
from src.card import Card

import os
import configparser

config_file_path = os.path.join(os.path.dirname(__file__), '..', 'config.ini')
config = configparser.ConfigParser()
config.read(config_file_path)
DISCONNECT_MESSAGE = config.get('SYSTEM CONFIG', 'DISCONNECT_MESSAGE')


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
        while self.running:
            event = self.deque_popleft()
            while event:
                self.print_update(event)
                event = self.deque_popleft()

    def print_update(self, event):
        event = json.loads(event)
        print("------------------------------------------")
        if "error" in event:
            print(event["error"])
            return
        if "announcement" in event:
            print(event["announcement"])
            return
        if "player_info" in event:
            print(f"{event['player_info']['name']}'s cards:")
            cards = event['player_info']['cards']
            cards.sort()
            scr = Card.system_cards_range
            for card in self.cards[:scr[0] - scr[1]]:
                print(self.card_to_human(card), end=', ')
            print()
            return
        if "winner" in event:
            print(f"Player {event['winner']['name']} won!")
            self.send(DISCONNECT_MESSAGE)
            self.thread_listen.join()
            self.thread_update.join()
            self.running = False
            return
        for player in event["info"]["players"]:
            print(
                f"{player['turn_id'] + 1}. {player['name']}: {player['cards_amount']} cards")
        card_id = event['info']['top_card_id']
        color = event['info']['top_card_color']
        print(f"Last played card: {color}_{Card(card_id).type}")

        turn = event['info']['turn']
        if turn == "you":
            print("It's your turn.", end=" ")
        else:
            print(
                f"It's {event['info']['players'][turn]['name']}\'s turn. ", end='')
        if event['info']['is_direction_clockwise']:
            print("The direction is clockwise")
        else:
            print("The direction is COUNTERclockwise")
        print()
        print("Your cards:")
        self.cards = event['info']['my_cards']
        self.cards.sort()
        scr = Card.system_cards_range
        for card in self.cards[:scr[0] - scr[1] - 1]:
            print(self.card_to_human(card), end=', ')
        print(self.card_to_human(self.cards[scr[0] - scr[1] - 1]), end='.\n')
        if event['info']['choosing']:
            print(
                "You need to choose color / accept or challenge / player to swap decks with")

    def listen_for_input(self):
        while True:
            inp = input()
            if self.correct_play(inp):
                pool = self.human_to_card(inp)
                for card in self.cards:
                    if card in pool:
                        self.send(str(card))
                        break
            else:
                print("That's not the correct play")

    def card_to_human(self, card_id) -> str:
        card = Card(card_id)
        if card_id >= Card.system_cards_range[0]:
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
