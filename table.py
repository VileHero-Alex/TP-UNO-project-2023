from deck import DrawDeck, TableDeck
from player import Player
from card import Card
import json
import random
from collections import deque

class Table():
    def __init__(self, players: list):
        self.players = players
        self.drawDeck = DrawDeck()
        self.tableDeck = TableDeck()
        self.turn = random.randint(0, len(players) - 1)
        self.is_direction_lockwise = True
        self.running = True
        for player in self.players:
            for i in range(7):
                card = self.drawDeck.pop_top()
                player.deck.receive_card(card)
    
    def reshuffle(self):
        if len(self.drawDeck) <= 1:
            cards = self.tableDeck.clear()
            for card in cards:
                self.drawDeck.recieve_card(card)
            self.drawDeck.shuffle()
    
    def draw(self, player: Player, amount: int) -> None:
        for i in range(amount):
            self.reshuffle()
            card = self.drawDeck.pop_top()
            player.deck.recieve(card)
        self.turn = self.next_turn()
    
    def listen(self):
        while self.running:
            for player_id in len(self.players):
                event = self.players[player_id].deque_popleft()
                try:
                    card = int(event)
                except Exception as e:
                    print(e)
                    continue
                self.make_move(player_id, card)
                
    def make_move(self, player_id: int, card: int):
        color_pool = ["red", "yellow", "green", "blue", "black"]
        type_pool = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "skip", "reverse", "+2"]
        type_pool_extra = ["uno", "draw", "red", "yellow", "green", "blue"]
        
        card = Card(card)
        if player_id == self.turn:
            if card.type in type_pool_extra:
                if card.type == "uno":
                    self.players[player_id].said_uno = True
                elif card.type == "draw":
                    self.draw(self.playerz[player_id], 1)
                    self.next_turn()
        else:
            pass


    def end_game(self):
        pass

    def select_color(self):
        color = self.players[self.turn].chooseColor()
        self.tableDeck.changeTopCardColor(color)
        self.updatePlayers()
    
    def change_direction(self):
        self.isDirectionClockwise = not self.isDirectionClockwise
    
    def next_turn(self):
        if self.isDirectionClockwise:
            next_player = (self.turn + 1) % len(self.players)
        else:
            next_player = (self.turn + len(self.players) - 1) % len(self.players)
        return next_player

    
    def game_info(self):
        players_info = []
        for player in self.players:
            info = {
                "id": player.id,
                "name": player.name,
                "cards_amount": len(player.deck)
            }
            players_info.append(info)
        my_dict = {
            "top_card": self.tableDeck.showLast.id,
            "players": players_info,
            "turn": self.turn,
            "isDirectionClockwise": self.isDirectionClockwise,
        }
        return json.dumps(my_dict)
    
    def updatePlayers(self):
        for player in self.players:
            player.update(self.game_info())

if __name__ == "__main__":
    table = Table()