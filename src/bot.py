import json
import threading
import time
import random
from src.client import Client
from src.card import Card

import os
import configparser
config_file_path = os.path.join(os.path.dirname(__file__), '..', 'config.ini')
config = configparser.ConfigParser()
config.read(config_file_path)
DISCONNECT_MESSAGE = config.get('SYSTEM CONFIG', 'DISCONNECT_MESSAGE')


class Bot(Client):
    BOT_NAMES = ['Max', 'Ace', 'Jazz', 'Arrow', 'Bolt', 'Domino', 'Ninja', 'Flip', 'Spark', 'Byte', 'Whirl', 'Botz', 'Chico', 'Darling', 'Gigabyte', 'Matrix',
                 'Nexus', 'Oracle', 'Quiver', 'Ranger', 'Phoenix', 'Speedy', 'Tangle', 'Upgrade', 'Vector', 'Wizard', 'Phantom', 'Zoom', 'Astro', 'Skillz', 'Luna']

    def __init__(self, deque_lock: threading.Lock, *, conn=None, server=None, port=None, name=''):
        super().__init__(deque_lock, conn=conn, server=server, port=port, name=name)
        self.thread_update = threading.Thread(target=self.listen_for_updates)
        self.running = True
        self.thread_update.start()

    def listen_for_updates(self):
        while self.running:
            event = self.deque_popleft()
            while event:
                self.process_move(event)
                event = self.deque_popleft()

    def process_move(self, event):
        event = json.loads(event)
        if "winner" in event:
            self.running = False
            self.send(DISCONNECT_MESSAGE)
            self.thread_update.join()
            return
        if "info" not in event:
            return
        info = event["info"]
        turn = info['turn']
        top_card = Card(info["top_card_id"])
        top_card.color = info["top_card_color"]
        players = info["players"]
        self.cards = info["my_cards"]
        choosing = info["choosing"]
        if turn != "you":
            self.process_send("uno", 1, 2)
            return

        if choosing:
            if top_card.type == "+4" and top_card.color != "black":
                action = random.choice(["accept", "challenge"])
                self.process_send(action)
            elif (top_card.type == "+4" and top_card.color == "black") or top_card.type == "choose":
                action = random.choice(["red", "yellow", "green", "blue"])
                self.process_send(action)
            elif top_card.type == "7":
                action = random.randint(1, len(players))
                self.process_send(str(action))
            return
        self.cards.sort()
        scr = Card.system_cards_range
        excluding_system = self.cards[:scr[0] - scr[1]]
        random.shuffle(excluding_system)
        for card_id in excluding_system:
            card = Card(card_id)
            if card.type == top_card.type or card.color == top_card.color or card.color == "black":
                action = card.color + "_" + card.type
                self.process_send(action)
                if len(excluding_system) == 2:
                    self.process_send('uno', 1, 2)
                return
        self.process_send("draw", 0.5, 1.5)

    def process_send(self, action, a=1, b=5):
        wait = 0
        mean = (a + b) / 2
        std_dev = (b - a) / 3.4
        while a < b and (wait < a or b < wait):
            wait = random.normalvariate(mean, std_dev)
        time.sleep(wait)
        pool = self.human_to_card(action)
        for card in self.cards:
            if card in pool:
                self.send(str(card))
                break

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
