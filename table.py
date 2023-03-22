from deck import DrawDeck, TableDeck
from player import Player
from card import Card
from errors import IllegalMove, CardError, InputError, Announcement, Skip
import json
import random
import time
import threading


class Table():
    def __init__(self, players: list, *, seven_zero=False, jump_in=False,
                 force_play=False, no_bluffing=False, draw_to_match=False):
        self.seven_zero = seven_zero
        self.jump_in = jump_in
        self.force_play = force_play
        self.no_bluffing = no_bluffing
        self.draw_to_match = draw_to_match

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
            for i in range(3):
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
    
    def draw(self, player: int, amount: int) -> None:
        for i in range(amount):
            self.reshuffle()
            card = self.drawDeck.pop_top()
            self.players[player].deck.receive_card(card)
        if len(self.players[player].deck) >= 2:
            self.players[player].said_uno = False
    
    def listen(self):
        while self.running:
            for player_id in range(len(self.players)):
                event = self.players[player_id].deque_popleft()
                while event:
                    try:
                        self.make_move(player_id, event)
                        if len(self.players[player_id].deck) == 0:
                            self.end_game(player_id)
                        else:
                            self.update_players()
                    except Exception as e:
                        self.update_player(player_id, error=str(e))
                    event = self.players[player_id].deque_popleft()
                
    def make_move(self, player_id: int, event: str):
        card = Card(int(event))
        if card.id not in self.players[player_id].deck.cards:
            raise IllegalMove("You don't have that card in your deck")
        
        if card.type == 'uno':
            if len(self.players[self.previous_turn()].deck) == 1 and not self.players[self.previous_turn()].said_uno:
                self.draw(self.previous_turn(), 2)
                self.update_players(announcement=f"{self.previous_turn()} was penalized for not saying UNO")
            elif self.turn == player_id and len(self.players[player_id].deck) == 1 and not self.players[self.previous_turn()].said_uno:
                self.players[player_id].said_uno = True
                self.update_players(announcement=f"{self.turn()} said UNO")
                raise Skip()

        if player_id == self.turn:
            if card.type == "black" and card.type in Card.type_pool_extra:
                if card.type == "draw":
                    if self.force_play and self.players[self.turn].deck.can_play(self.tableDeck.show_last(), self.tableDeck.top_color):
                        raise IllegalMove("Force play is enabled, you can (and should) play a card from your deck")
                    self.draw(player_id, 1)
                    if not self.draw_to_match:
                        self.turn = self.next_turn()

                elif card.type in Card.color_pool[:-1] and self.tableDeck.top_color == "black":
                    self.players[player_id].is_choosing = False
                    self.tableDeck.top_color = card.type
                    self.turn = self.next_turn()
                    if Card(self.tableDeck.show_last()).type == "+4" and self.no_bluffing:
                        self.turn = self.next_turn()
                        self.players[self.turn].is_choosing = True
                    
                elif card.type == "challenge" or card.type == "accept":
                    if self.no_bluffing:
                        raise IllegalMove("No bluffing mode is enabled")
                    if Card(self.tableDeck.show_last()).type != '+4':
                        raise IllegalMove("You can't use that now")
                    self.players[player_id].is_choosing = False
                    if card.type == "challenge":
                        self.update_players(announcement=f"{player_id} challenges {self.previous_turn}")
                        self.update_player(player_id, show_cards=self.previous_turn())
                        if self.players[self.previous_turn()].deck.can_play(self.tableDeck.show_last(), self.tableDeck.top_color):
                            self.update_players(announcement=f"Challenge succesful")
                            self.draw(self.previous_turn(), 4)
                        else:
                            self.update_players(announcement=f"Challenge failed")
                            self.draw(self.turn, 6)
                            self.turn = self.next_turn()
                    else:
                        self.draw(self.turn, 4)
                        self.turn = self.next_turn()
                elif card.type in ["1", "2", "3", "4"] and Card(self.tableDeck.show_last).type == '7':
                    self.seven(player_id, int(card.type) - 1)
                    self.players[player_id].is_choosing = False
                    self.turn = self.next_turn()

            elif card.type == "+4":
                if self.no_bluffing:
                    self.draw(self.next_turn(), 4)
                self.lay_card(player_id, card)
                self.players[player_id].is_choosing = True
                
            elif card.type == "choose":
                self.lay_card(player_id, card)
                self.players[player_id].is_choosing = True

            elif card.color == self.tableDeck.top_color or Card(self.tableDeck.show_last()).type == card.type:
                self.lay_card(player_id, card)
                if card.type == "skip":
                    self.turn = self.next_turn()
                elif card.type == "reverse":
                    self.change_direction()
                elif card.type == "+2":
                    self.turn = self.next_turn()
                    self.draw(self.turn, 2)
                elif card.type == "0":
                    self.zero()

                if card.type != "7":
                    self.turn = self.next_turn()
                else:
                    self.players[player_id].is_choosing = True
            else:
                raise IllegalMove("IllegalMove")
        
        else:
            if card.color == self.tableDeck.top_color and Card(self.tableDeck.show_last()).type == card.type and card.type in Card.type_pool[:-2]:
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

    def zero(self):
        for i in range(len(self.players) - 1):
            self.players[i].deck, self.players[i + 1].deck = self.players[i + 1].deck, self.players[i].deck
    
    def seven(self, player_one, player_two):
        self.players[player_one].deck, self.players[player_two].deck = self.players[player_two].deck, self.players[player_one].deck
    
    def lay_card(self, player_id, card):
        self.players[player_id].deck.throw_card(card.id)
        if len(self.players[player_id].deck) >= 2:
            self.players[player_id].said_uno = False
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

    def update_player(self, receiver_player_id, *, winner_id=None, error=None, show_cards=None, announcement=None):
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
        
        if winner_id:
            message = {
                "status": "finished",
                "winner": players_info[winner_id],
            }
        elif error:
            message = {
                "status": "running",
                "error": str(error)
            }
        elif announcement:
            message = {
                "status": "running",
                "announcement": announcement,
            }
        else:
            message = {
                "status": "running",
                "info": {
                    "top_card_id": self.tableDeck.show_last(),
                    "top_card_color": self.tableDeck.top_color,
                    "players": players_info,
                    "turn": "you" if receiver_player_id == self.turn else self.turn,
                    "is_direction_clockwise": self.is_direction_clockwise,
                    "my_cards": self.players[receiver_player_id].deck.cards,
                }
            }
        # pp.pprint(message)
        self.players[receiver_player_id].send(json.dumps(message))
    
    def update_players(self, winner_id=None, announcement=None):
        for player_id in range(len(self.players)):
            self.update_player(player_id, winner_id=winner_id, announcement=announcement)

if __name__ == "__main__":
    table = Table()