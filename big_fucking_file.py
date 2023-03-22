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


class Card:
    color_pool = ["red", "yellow", "green", "blue", "black"]
    type_pool = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "skip", "reverse", "+2", "choose", "+4"]
    type_pool_extra = ["uno", "draw", "red", "yellow", "green", "blue"]

    def __init__(self, id):
        self.id = id
        color, type = self.card_identificator(id)
        self.color = color
        self.type = type

    def card_identificator(self, id):
        color = Card.color_pool[id // 25]
        
        if id % 25 == 0 and id != 100:
            type = "0"
        elif 104 <= id <= 107:
            type = "+4"
        elif 100 <= id <= 103:
            type = "choose"
        elif id >= 108:
            type = Card.type_pool_extra[id - 108]
        else:
            type = Card.type_pool[(id % 25 + 1) // 2] 

        return (color, type)

    def system_cards_range():
        return (108, 114)


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

    def show_last(self) -> int:
        if self.is_empty():
            return None
        return self.cards[-1]
    
    def clear(self) -> None:
        last_card_id = self.cards[-1]
        self.cards.pop()
        removed_cards = self.cards.copy()
        self.cards = [last_card_id]
        return removed_cards
    
    def receive_card(self, receive_card_id: int) -> None:
        self.top_color = Card(receive_card_id).color
        self.cards.append(receive_card_id)


class PlayerDeck(Deck):
    def __init__(self):
        scr = Card.system_cards_range()
        self.cards = [i for i in range(scr[0], scr[1])] # system cards
    
    def __len__(self):
        scr = Card.system_cards_range()
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


class PopCardError(Exception):
    pass

class IllegalMove(Exception):
    pass


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
        self.time_since_uno = time.time()

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
            print(f"[NEW CONNECTION] {addr} connected.")
            # print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 2}")


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
                    self.draw(player_id, 1)
                    self.turn = self.next_turn()

                elif card.type in Card.type_pool_extra and self.tableDeck.top_color == "black":
                    self.tableDeck.top_color = card.type
                    self.turn = self.next_turn()
                    if Card(self.tableDeck.show_last()).type == "+4":
                        self.turn = self.next_turn()

            elif card.type == "+4":
                self.draw(self.next_turn(), 4)
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
                    self.draw(self.next_turn(), 2)
                    self.turn = self.next_turn()

                self.turn = self.next_turn()

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

    
    def update_player(self, receiver_player_id, *, winner_id=None, error=None):
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
            "turn": "you" if receiver_player_id == self.turn else self.turn,
            "is_direction_clockwise": self.is_direction_clockwise,
            "my_cards": self.players[receiver_player_id].deck.cards,
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
        # pp.pprint(my_dict_final)
        self.players[receiver_player_id].send(json.dumps(my_dict_final))
    
    def update_players(self, winner_id=None):
        for player_id in range(len(self.players)):
            self.update_player(player_id, winner_id=winner_id)