from deck import DrawDeck, TableDeck
from player import Player
from card import Card
import json
import random
import time

class IllegalMove(Exception):
    pass

class Table():
    def __init__(self, players: list):
        self.players = players
        self.drawDeck = DrawDeck()
        self.tableDeck = TableDeck()
        self.tableDeck.recieve_card(self.tableDeck.pop_top())
        self.turn = random.randint(0, len(players) - 1)
        self.is_direction_clockwise = True
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
                try:
                    self.make_move(player_id, card)
                except IllegalMove:
                    self.players[player_id].send("IllegalMove") # TODO
                
    def make_move(self, player_id: int, card: int):
        color_pool = ["red", "yellow", "green", "blue", "black"]
        type_pool = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "skip", "reverse", "+2"]
        type_pool_extra = ["uno", "draw", "red", "yellow", "green", "blue"]
        
        card = Card(card)
        if card not in self.players[player_id].deck.cards:
            return
        if player_id == self.turn:
            if card.type in type_pool_extra:
                if card.type == "uno":
                    self.players[player_id].said_uno = True
                    self.players[player_id].time_since_uno = time.time()

                elif card.type == "draw":
                    self.draw(self.players[player_id], 1)
                    self.turn = self.next_turn()

                elif card.type in type_pool_extra and self.tableDeck.top_color == "black":
                    self.tableDeck.top_color = card.type
                    self.turn = self.next_turn()

            elif card.type == "+4":
                next_player = self.next_turn()
                self.draw(self.players[next_player], 4)
                self.lay_card(player_id, card)
                
            elif card.type == "choose":
                self.lay_card(player_id, card)

            elif card.color == self.tableDeck.top_color or self.tableDeck.show_last().type == card.type:
                self.lay_card(player_id, card)
                if card.type == "skip":
                    self.turn = self.next_turn()

                elif card.type == "reverse":
                    self.change_direction()

                elif card.type == "+2":
                    next_player = self.next_turn()
                    self.draw(self.players[next_player], 2)

                self.turn = self.next_turn()

            else:
                raise IllegalMove("IllegalMove")
        else:
            if card.color == self.tableDeck.top_color and self.tableDeck.show_last().type == card.type and card.type in [str(i) for i in range(1, 10)]:
                self.lay_card(player_id, card)
                self.turn = player_id
                self.turn = self.next_turn()
            elif card.type == "uno":
                if len(self.players[self.previous_turn()].deck) == 1 \
                        and not self.players[self.previous_turn()].said_uno:
                    self.draw(self.previous_turn(), 2)
                    self.players[self.previous_turn()].said_uno = True
                elif time.time() - self.players[self.previous_turn()].time_since_uno < 5:
                    pass
                else:
                    self.draw(player_id, 2)
            else:
                raise IllegalMove("IllegalMove")
        
        
            
    
    def lay_card(self, player_id, card):
        self.players[player_id].deck.throw_card(card.id)
        self.tableDeck.receive_card(card.id)

    def end_game(self):
        pass

    def select_color(self):
        color = self.players[self.turn].chooseColor()
        self.tableDeck.changeTopCardColor(color)
        self.updatePlayers()
    
    def change_direction(self):
        self.is_direction_clockwise = not self.is_direction_clockwise
    
    def previous_turn(self):
        self.change_direction()
        prev_turn = self.next_turn()
        self.change_direction()
        return prev_turn
    
    def next_turn(self):
        if self.is_direction_clockwise:
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
            "is_direction_clockwise": self.is_direction_clockwise,
        }
        return json.dumps(my_dict)
    
    def updatePlayers(self):
        for player in self.players:
            player.update(self.game_info())

if __name__ == "__main__":
    table = Table()