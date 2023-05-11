import json
import random
import time
import threading
from src.deck import DrawDeck, TableDeck
from src.card import Card
from src.errors import IllegalMove

import os
import configparser

config_file_path = os.path.join(os.path.dirname(__file__), '..', 'config.ini')
config = configparser.ConfigParser()
config.read(config_file_path)

INITIAL_NUMBER_OF_CARDS = config.getint(
    'GAME RULES', 'INITIAL_NUMBER_OF_CARDS')
SEVEN_ZERO = config.getboolean('GAME RULES', 'SEVEN_ZERO')
JUMP_IN = config.getboolean('GAME RULES', 'JUMP_IN')
FORCE_PLAY = config.getboolean('GAME RULES', 'FORCE_PLAY')
NO_BLUFFING = config.getboolean('GAME RULES', 'NO_BLUFFING')
DRAW_TO_MATCH = config.getboolean('GAME RULES', 'DRAW_TO_MATCH')
STACKING = config.getboolean('GAME RULES', 'STACKING')


class Table():
    def __init__(self, players: list):
        self.players = players
        self.drawDeck = DrawDeck()
        self.tableDeck = TableDeck()
        self.stack = 0
        while Card(self.drawDeck.cards[0]).color == 'black':
            self.drawDeck = DrawDeck()
        self.tableDeck.receive_card(self.drawDeck.pop_top())
        self.turn = random.randint(0, len(players) - 1)
        self.is_direction_clockwise = True
        self.running = True
        for player in self.players:
            for i in range(INITIAL_NUMBER_OF_CARDS):
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
                        self.update_players()
                        self.end_game()
                    except Exception as e:
                        self.update_player(player_id, error=str(e))
                    event = self.players[player_id].deque_popleft()
        self.thread.join()

    def make_move(self, player_id: int, event: str):
        card = Card(int(event))
        if card.id not in self.players[player_id].deck.cards:
            raise IllegalMove("You don't have that card in your deck")

        if card.type == 'uno':
            if len(self.players[self.previous_turn()].deck) == 1 and \
                not self.players[self.previous_turn()].said_uno:

                if player_id == self.previous_turn():
                    self.players[player_id].said_uno = True
                    self.update_players(
                        announcement=f"Player {player_id + 1} said UNO")
                    return
                self.draw(self.previous_turn(), 2)
                self.update_players(
                    announcement=f"{self.previous_turn()} was penalized \
                                   for not saying UNO"
                )
                return
            elif self.turn == player_id and \
                len(self.players[player_id].deck) == 1 and \
                not self.players[self.previous_turn()].said_uno:

                self.players[player_id].said_uno = True
                self.update_players(
                    announcement=f"Player {player_id + 1} said UNO")
                return
            else:
                raise IllegalMove("You can't use 'uno' now")
        if card.id < Card.system_cards_range[0] + 2 and \
            self.players[player_id].is_choosing:

            raise IllegalMove(
                "You need to choose color / accept or challenge / \
                player to swap decks with"
            )

        if player_id == self.turn:
            if card.id >= Card.system_cards_range[0]:
                if card.type == "draw":
                    if FORCE_PLAY and self.players[self.turn].deck.can_play(
                            self.tableDeck.show_last(),
                            self.tableDeck.top_color,
                            check_for_black=True
                        ):
                        raise IllegalMove(
                            "Force play is enabled, you can (and should) \
                            play a card from your deck"
                        )
                    self.draw(player_id, 1)
                    if not DRAW_TO_MATCH:
                        self.turn = self.next_turn()
                elif not self.players[player_id].is_choosing:
                    raise IllegalMove("The fuck are you choosing")
                elif card.type in Card.color_pool[:-1] and \
                    self.tableDeck.top_color == "black":

                    self.players[player_id].is_choosing = False
                    self.tableDeck.top_color = card.type
                    self.turn = self.next_turn()
                    if Card(self.tableDeck.show_last()).type == "+4":
                        if NO_BLUFFING:
                            self.draw(self.turn, 4)
                            self.turn = self.next_turn()
                        else:
                            self.players[self.turn].is_choosing = True

                elif (card.type == "challenge" or card.type == "accept") and \
                    self.tableDeck.top_color != "black":

                    if NO_BLUFFING:
                        raise IllegalMove("No bluffing mode is enabled")
                    if Card(self.tableDeck.show_last()).type != '+4':
                        raise IllegalMove("You can't use that now")
                    self.players[player_id].is_choosing = False
                    if card.type == "challenge":
                        self.update_players(
                            announcement=f"Player {player_id + 1} challenges \
                                           Player {self.previous_turn() + 1}"
                        )
                        self.update_player(
                            player_id, show_cards=self.previous_turn()+1)
                        if self.players[self.previous_turn()].deck.can_play(
                                self.tableDeck.show_before_last(),
                                self.tableDeck.last_top_color
                            ):
                            self.update_players(
                                announcement=f"Challenge succesful")
                            self.draw(self.previous_turn(), 4)
                        else:
                            self.update_players(
                                announcement=f"Challenge failed")
                            self.draw(self.turn, 6)
                            self.turn = self.next_turn()
                    else:
                        self.draw(self.turn, 4)
                        self.turn = self.next_turn()
                elif card.type in ["1", "2", "3", "4"] and \
                    Card(self.tableDeck.show_last()).type == '7':

                    if not SEVEN_ZERO:
                        raise IllegalMove("7-0 mode is not enabled")
                    if player_id == int(card.type) - 1:
                        raise IllegalMove("You can't swap cards with yourself")
                    if int(card.type) > len(self.players):
                        raise IllegalMove(f"Player {card.type} doesn't exist")
                    self.update_players(
                        announcement=f"Player {player_id + 1} swaps cards with \
                                       Player {int(card.type)}"
                    )
                    self.seven(player_id, int(card.type) - 1)
                    self.players[player_id].is_choosing = False
                    self.turn = self.next_turn()
                else:
                    raise IllegalMove("Illegal move")

            elif card.type == "+4":
                if NO_BLUFFING:
                    self.draw(self.next_turn(), 4)
                self.lay_card(player_id, card)
                self.players[player_id].is_choosing = True

            elif card.type == "choose":
                self.lay_card(player_id, card)
                self.players[player_id].is_choosing = True

            elif card.color == self.tableDeck.top_color or \
                Card(self.tableDeck.show_last()).type == card.type:

                self.lay_card(player_id, card)
                if card.type == "skip":
                    self.turn = self.next_turn()
                elif card.type == "reverse":
                    self.change_direction()
                elif card.type == "+2":
                    self.stack += 2
                    self.turn = self.next_turn()
                    if STACKING:
                        if not self.players[self.turn].has_2():
                            self.draw(self.turn, self.stack)
                            self.stack = 0
                    else:
                        self.draw(self.turn, self.stack)
                        self.stack = 0
                elif card.type == "0" and SEVEN_ZERO and \
                     len(self.players[player_id].deck) != 0:
                    self.change_direction()
                    self.zero()
                    self.change_direction()
                if card.type == "7" and SEVEN_ZERO:
                    self.players[player_id].is_choosing = True
                else:
                    self.turn = self.next_turn()
            else:
                raise IllegalMove("Illegal move")

        else:
            if card.color == self.tableDeck.top_color and \
               Card(self.tableDeck.show_last()).type == card.type and \
               card.type in Card.type_pool[:-2]:

                if not JUMP_IN:
                    raise IllegalMove("Jump-in mode is not enabled")
                if any([player.is_choosing for player in self.players]):
                    raise IllegalMove(
                        "You have to wait until the person will choose color / \
                         challenge or accept / player to swap cards with"
                    )

                self.turn = player_id
                self.lay_card(player_id, card)
                if card.type == "skip":
                    self.turn = self.next_turn()
                elif card.type == "reverse":
                    self.change_direction()
                elif card.type == "+2":
                    self.stack += 2
                    self.turn = self.next_turn()
                    if STACKING:
                        if not self.players[self.turn].has_2():
                            self.draw(self.turn, self.stack)
                            self.stack = 0
                    else:
                        self.draw(self.turn, self.stack)
                        self.stack = 0
                elif card.type == "0" and SEVEN_ZERO and \
                    len(self.players[player_id].deck) != 0:

                    self.change_direction()
                    self.zero()
                    self.change_direction()
                if card.type == "7" and SEVEN_ZERO:
                    self.players[player_id].is_choosing = True
                else:
                    self.turn = self.next_turn()
            else:
                raise IllegalMove("Illegal move")

    def zero(self):
        for i in range(len(self.players) - 1):
            self.seven(i, i + 1)

    def seven(self, player_one, player_two):
        self.players[player_one].deck, self.players[player_two].deck = \
        self.players[player_two].deck, self.players[player_one].deck

    def lay_card(self, player_id, card):
        self.players[player_id].deck.throw_card(card.id)
        if len(self.players[player_id].deck) >= 2:
            self.players[player_id].said_uno = False
        self.tableDeck.receive_card(card.id)

    def end_game(self):
        for player_id in range(len(self.players)):
            if len(self.players[player_id].deck) == 0:
                self.update_players(winner_id=player_id)
                self.running = False

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
            next_player = (self.turn + len(self.players) -
                           1) % len(self.players)
        return next_player

    def update_player(self, receiver_player_id, *,
                      winner_id=None, error=None,
                      show_cards=None, announcement=None):
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
        elif show_cards:
            player = self.players[show_cards-1]
            message = {
                "status": "running",
                "player_info": {
                    "turn_id": show_cards-1,
                    "id": player.id,
                    "name": player.name,
                    "cards": player.deck.cards
                }
            }
        else:
            message = {
                "status": "running",
                "info": {
                    "top_card_id": self.tableDeck.show_last(),
                    "top_card_color": self.tableDeck.top_color,
                    "players": players_info,
                    "turn": self.turn,
                    "is_direction_clockwise": self.is_direction_clockwise,
                    "my_cards": self.players[receiver_player_id].deck.cards,
                    "choosing": self.players[receiver_player_id].is_choosing,
                }
            }
            if receiver_player_id == self.turn:
                message["info"]["turn"] = "you"
        # pp.pprint(message)
        self.players[receiver_player_id].send(json.dumps(message))

    def update_players(self, winner_id=None, announcement=None):
        for player_id in range(len(self.players)):
            self.update_player(player_id, winner_id=winner_id,
                               announcement=announcement)


if __name__ == "__main__":
    table = Table()
