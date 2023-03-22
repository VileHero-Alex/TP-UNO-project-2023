from deck import DrawDeck, TableDeck
from player import Player
from card import Card
from errors import IllegalMove
import json
import random
import time
import threading


class Table():
    def __init__(self, players: list):
        self.players = players
        self.drawDeck = DrawDeck()
        self.tableDeck = TableDeck()
        while Card(self.drawDeck.cards[0]).color == 'black':
            self.drawDeck = DrawDeck()
            print("Ooops)")
        self.tableDeck.receive_card(self.drawDeck.pop_top())
        self.turn = random.randint(0, len(players) - 1)
        self.is_direction_clockwise = True
        self.running = True
        for player in self.players:
            for i in range(7):
                card = self.drawDeck.pop_top()
                player.deck.receive_card(card)
        self.update_players()
        self.thread = threading.Thread(target=self.listen)
        self.thread.start()
    
    def reshuffle(self):
        if len(self.drawDeck) <= 1:
            cards = self.tableDeck.clear()
            for card in cards:
                self.drawDeck.receive_card(card)
            self.drawDeck.shuffle()
    
    def draw(self, player: Player, amount: int) -> None:
        for i in range(amount):
            self.reshuffle()
            card = self.drawDeck.pop_top()
            player.deck.receive_card(card)
        self.turn = self.next_turn()
    
    def listen(self):
        while self.running:
            for player_id in range(len(self.players)):
                event = self.players[player_id].deque_popleft()
                while event:
                    try:
                        card = int(event)
                    except Exception as e:
                        print(e)
                        continue
                    try:
                        self.make_move(player_id, card)
                        if len(self.players[player_id].deck) == 0:
                            self.end_game(player_id)
                        else:
                            self.update_players()
                    except IllegalMove:
                        self.update_player(player_id, error="Illegal move")
                    event = self.players[player_id].deque_popleft()
                
    def make_move(self, player_id: int, card: int):
        card = Card(card)
        if card.id not in self.players[player_id].deck.cards:
            print(self.players[player_id].deck.cards, card)
            raise IllegalMove("Illegal move")
        if player_id == self.turn:
            if card.type in Card.type_pool_extra:
                if card.type == "uno":
                    self.players[player_id].said_uno = True
                    self.players[player_id].time_since_uno = time.time()

                elif card.type == "draw":
                    self.draw(self.players[player_id], 1)
                    self.turn = self.next_turn()

                elif card.type in Card.type_pool_extra and self.tableDeck.top_color == "black":
                    self.tableDeck.top_color = card.type
                    self.turn = self.next_turn()

            elif card.type == "+4":
                next_player = self.next_turn()
                self.draw(self.players[next_player], 4)
                self.lay_card(player_id, card)
                
            elif card.type == "choose":
                self.lay_card(player_id, card)

            elif card.color == self.tableDeck.top_color or Card(self.tableDeck.show_last()).type == card.type:
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
            if card.color == self.tableDeck.top_color and Card(self.tableDeck.show_last()).type == card.type and card.type in [str(i) for i in range(1, 10)]:
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

    def end_game(self, player_id):
        self.update_players(winner_id=player_id)
        self.runnning = False
    
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

    
    def update_player(self, player_id, *, winner_id=None, error=None):
        players_info = []
        for player_id in range(len(self.players)):
            player = self.players[player_id]
            info = {
                "turn_id": player_id,
                "id": player.id,
                "name": player.name,
                "cards_amount": len(player.deck)
            }
            players_info.append(info)

        my_dict = {
            "top_card_id": self.tableDeck.show_last(),
            "top_card_color": self.tableDeck.top_color,
            "players": players_info,
            "turn": "you" if player_id == self.turn else self.turn,
            "is_direction_clockwise": self.is_direction_clockwise,
            "my_cards": self.players[player_id].deck.cards,
        }
        if winner_id:
            my_dict_final = {
                "ok": True,
                "status": "finished",
                "winner": players_info[winner_id],
            }
        elif error:
            my_dict_final = {
                "ok": False,
                "error": str(error)
            }
        else:
            my_dict_final = {
                "ok": True,
                "status": "running",
                "info": my_dict
            }
        self.players[player].send(json.dumps(my_dict_final))
    
    def update_players(self, winner_id=None):
        for player_id in range(len(self.players)):
            self.update_player(player_id, winner_id=winner_id)

if __name__ == "__main__":
    table = Table()