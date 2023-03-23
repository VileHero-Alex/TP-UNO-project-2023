import random
from card import Card
from errors import PopCardError


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