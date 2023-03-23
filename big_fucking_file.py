import random
import socket
import threading
from collections import deque
import json
import time
import pprint
pp = pprint.PrettyPrinter(indent=4)

HEADER = 64
PORT = 5050
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "beep boop, disconnected"
SERVER = "192.168.50.17"

class PopCardError(Exception):
    pass

class IllegalMove(Exception):
    pass

class InputError(Exception):
    pass
class Skip(Exception):
    pass

class Card:
    color_pool = ["red", "yellow", "green", "blue", "black"]
    type_pool = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "skip", "reverse", "+2", "choose", "+4"]
    type_pool_extra = ["uno", "draw", "red", "yellow", "green", "blue", "challenge", "accept", "1", "2", "3", "4"]
    system_cards_range = (108, 120)

    def __init__(self, card_id: int):
        try:
            if card_id >= Card.system_cards_range[1]:
                raise InputError(f"Card with that ID ({card_id}) doesn't exist")
        except Exception as e:
            print(e)
            raise e
        self.id = card_id
        color, type = self.card_identificator(card_id)
        self.color = color
        self.type = type

    def card_identificator(self, card_id):
        color = Card.color_pool[card_id // 25]
        
        if card_id % 25 == 0 and card_id != 100:
            type = "0"
        elif 104 <= card_id <= 107:
            type = "+4"
        elif 100 <= card_id <= 103:
            type = "choose"
        elif card_id >= 108:
            type = Card.type_pool_extra[card_id - 108]
        else:
            type = Card.type_pool[(card_id % 25 + 1) // 2]

        return (color, type)


class Deck:
    def __init__(self):
        self.cards = []

    def __len__(self):
        return len(self.cards)
    
    def pop_card(self, pop_card_id) -> int:
        try:
            self.cards.remove(pop_card_id)
            return pop_card_id
        except:
            raise PopCardError("illegal move: there is no card that you are looking for!")

    def receive_card(self, receive_card_id) -> None:
        self.cards.append(receive_card_id)

    def is_empty(self) -> bool:
        return len(self.cards) == 0


class DrawDeck(Deck):
    def __init__(self):
        self.cards = [i for i in range(108)]
        self.shuffle()

    def shuffle(self) -> None:
        random.shuffle(self.cards)
    
    def pop_top(self) -> int:
        received_card_id = self.pop_card(self.cards[0])
        return received_card_id

class TableDeck(Deck):
    def __init__(self):
        super().__init__()
        self.top_color = None
        self.last_top_color = None

    def show_last(self) -> int:
        if self.is_empty():
            return None
        return self.cards[-1]

    def show_before_last(self) -> int:
        if len(self) < 2:
            return None
        return self.cards[-2]
    
    def clear(self) -> None:
        last_card_id = self.cards[-1]
        self.cards.pop()
        last_after_last_card_id = self.cards[-1]
        self.cards.pop()
        removed_cards = self.cards.copy()
        self.cards = [last_after_last_card_id, last_card_id]
        return removed_cards
    
    def receive_card(self, receive_card_id: int) -> None:
        self.last_top_color = self.top_color
        self.top_color = Card(receive_card_id).color
        self.cards.append(receive_card_id)


class PlayerDeck(Deck):
    def __init__(self):
        scr = Card.system_cards_range
        self.cards = [i for i in range(scr[0], scr[1])] # system cards
    
    def __len__(self):
        scr = Card.system_cards_range
        rng = scr[1] - scr[0]
        return len(self.cards) - rng

    def sort(self) -> None:
        self.cards.sort()

    def throw_card(self, throw_card_id: int) -> None:
        try:
            return self.pop_card(throw_card_id)
        except PopCardError as err:
            print(err, " Try again.")
            return -1
    
    def can_play(self, top_id, top_color, check_for_black=False):
        top_card = Card(top_id)
        self.sort()
        scr = Card.system_cards_range
        for card_id in self.cards[:scr[0] - scr[1]]:
            card = Card(card_id)
            if card.color == "black" and check_for_black:
                return True
            if card.color == top_color or card.type == top_card.type:
                return True
        return False
    
    def has_plus(self, type: str): # '+2' or '+4' should be passed
        for card_id in self.cards:
            if Card(card_id).type == type:
                return True
        return False


class Client:
    def __init__(self, deque_lock: threading.Lock, *, conn=None, server=None, port=None, name=''):
        self.deque_lock = deque_lock
        self.deque = deque()
        if conn:
            self.conn = conn
            self.name = self.receive()
        else:
            self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.conn.connect((server, port))
            self.send(name)
            print("[CLIENT STARTUP] client is connected to {}:{}".format(server, port))
        self.thread = threading.Thread(target=self.wait_for_messages)
        self.thread.start()
        
    def send(self, data):
        message = data.encode(FORMAT)
        msg_length = len(message)
        send_length = str(msg_length).encode(FORMAT)
        send_length += b' ' * (HEADER - len(send_length))
        try:
            self.conn.send(send_length)
            self.conn.send(message)
        except BrokenPipeError or ConnectionAbortedError or ConnectionResetError or InterruptedError:
            self.send(self, data)
        
    def receive(self):
        msg_length = self.conn.recv(HEADER).decode(FORMAT)
        if msg_length:
            msg_length = int(msg_length)
            msg = self.conn.recv(msg_length).decode(FORMAT)
            return msg
        return None
    
    def wait_for_messages(self):
        connected = True
        while connected:
            try:
                msg = self.receive()
            except ConnectionError:
                connected = False
                break
            if msg:
                if msg == DISCONNECT_MESSAGE:
                    connected = False
                self.deque_append(msg)
        self.conn.close()
    
    def deque_append(self, msg):
        with self.deque_lock:
            self.deque.append(msg)
    
    def deque_popleft(self):
        try:
            with self.deque_lock:
                return self.deque.popleft()
        except IndexError:
            return None

class Player(Client):
    def __init__(self, deque_lock: threading.Lock, *, conn=None, server=None, port=None, name=''):
        super().__init__(deque_lock, conn=conn, server=server, port=port, name=name)
        self.id = hash(name)
        self.reinit()
    
    def reinit(self):
        self.deck = PlayerDeck()
        self.said_uno = False
        self.is_choosing = False

class Bot(Player):
    def update(self, info):
        self.status = json.loads(info)

class Server():
    def __init__(self, server, port, deque_lock=None):
        self.server = server
        self.port = port
        if deque_lock:
            self.deque_lock = deque_lock
        else:
            self.deque_lock = threading.Lock()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        while True:
            try:
                self.socket.bind((self.server, self.port))
                break
            except OSError:
                self.port += 1
        self.clients = []
        self.socket.listen(1)
        self.thread = threading.Thread(target=self.wait_for_connections)
        self.thread.start()
        print("[SERVER STARTUP] server is running on {}:{}".format(self.server, self.port))
        
    def wait_for_connections(self):
        while True:
            conn, addr = self.socket.accept()
            self.clients.append(Player(self.deque_lock, conn=conn))
            print(f"[NEW CONNECTION] {self.clients[-1].name}: {addr} connected.")
            # print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 2}")


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
                return
            elif self.turn == player_id and len(self.players[player_id].deck) == 1 and not self.players[self.previous_turn()].said_uno:
                self.players[player_id].said_uno = True
                self.update_players(announcement=f"{self.turn()} said UNO")
                return
        if card.id < Card.system_cards_range[0] + 2 and self.players[player_id].is_choosing:
            raise IllegalMove("You need to choose color / accept or challenge / player to swap decks with")

        if player_id == self.turn:
            if card.id >= Card.system_cards_range[0]:
                if card.type == "draw":
                    if self.force_play and self.players[self.turn].deck.can_play(self.tableDeck.show_last(), self.tableDeck.top_color, check_for_black=True):
                        raise IllegalMove("Force play is enabled, you can (and should) play a card from your deck")
                    self.draw(player_id, 1)
                    if not self.draw_to_match:
                        self.turn = self.next_turn()

                elif card.type in Card.color_pool[:-1] and self.tableDeck.top_color == "black":
                    self.players[player_id].is_choosing = False
                    self.tableDeck.top_color = card.type
                    self.turn = self.next_turn()
                    if Card(self.tableDeck.show_last()).type == "+4":
                        if self.no_bluffing:
                            self.draw(self.turn, 4)
                            self.turn = self.next_turn()
                        else:
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
                        if self.players[self.previous_turn()].deck.can_play(self.tableDeck.show_before_last(), self.tableDeck.last_top_color):
                            self.update_players(announcement=f"Challenge succesful")
                            self.draw(self.previous_turn(), 4)
                        else:
                            self.update_players(announcement=f"Challenge failed")
                            self.draw(self.turn, 6)
                            self.turn = self.next_turn()
                    else:
                        self.draw(self.turn, 4)
                        self.turn = self.next_turn()
                elif card.type in ["1", "2", "3", "4"] and Card(self.tableDeck.show_last()).type == '7':
                    if not self.seven_zero:
                        raise IllegalMove("7-0 mode is not enabled")
                    if player_id == int(card.type) - 1:
                        raise IllegalMove("You can't swap cards with yourself")
                    self.seven(player_id, int(card.type) - 1)
                    self.players[player_id].is_choosing = False
                    self.turn = self.next_turn()
                else:
                    raise IllegalMove("Illegal move")

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
                elif card.type == "0" and self.seven_zero:
                    self.zero()
                if card.type == "7" and self.seven_zero:
                    self.players[player_id].is_choosing = True
                else:
                    self.turn = self.next_turn()
            else:
                raise IllegalMove("Illegal move")
        
        else:
            if card.color == self.tableDeck.top_color and Card(self.tableDeck.show_last()).type == card.type and card.type in Card.type_pool[:-2]:
                if not self.jump_in:
                    raise IllegalMove("Jump-in mode is not enabled")
                if any([player.is_choosing for player in self.players]):
                    raise IllegalMove("You have to wait until the person will choose color / challenge or accept / player to swap cards with")
                
                self.lay_card(player_id, card)
                if card.type == "skip":
                    self.turn = self.next_turn()
                elif card.type == "reverse":
                    self.change_direction()
                elif card.type == "+2":
                    self.turn = self.next_turn()
                    self.draw(self.turn, 2)
                elif card.type == "0" and self.seven_zero:
                    self.zero()
                if card.type == "7" and self.seven_zero:
                    self.players[player_id].is_choosing = True
                else:
                    self.turn = self.next_turn()
            else:
                raise IllegalMove("Illegal move")

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
        elif show_cards:
            player = self.players[show_cards]
            message = {
                "status": "running",
                "player_info": {
                    "turn_id": show_cards,
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
