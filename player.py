from deck import PlayerDeck, TableDeck, DrawDeck
import json

class Player:
    def __init__(self, name, handle_turn):
        self.name = name
        self.id = hash(name)
        self.deck = PlayerDeck()
        self.handle_turn = handle_turn

class Bot(Player):
    def update(self, info):
        self.status = json.loads(info)