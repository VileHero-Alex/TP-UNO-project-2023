import random
from card import Card
from errors import PopCardError


class Deck:
    def __init__(self):
        self.cards = []

    def __len__(self):
        return len(self.cards)
    
    def pop_card(self, pop_card_id):
        try:
            self.cards.remove(pop_card_id)
            return pop_card_id
        except:
            raise PopCardError("illegal move: there is no card that you are looking for!")

    def receive_card(self, receive_card_id):
        self.cards.append(receive_card_id)


class DrawDeck(Deck):
    def __init__(self):
        self.cards = [i for i in range(108)]
        self.shuffle()

    def shuffle(self):
        random.shuffle(self.cards)
    
    def pop_top(self):
        received_card_id = self.pop_card(self.cards[0])
        return received_card_id

    def is_empty(self):
        return len(self.cards) == 0

class TableDeck(Deck):
    def __init__(self):
        super().__init__()
        self.top_color = None

    def show_last(self):
        if self.is_empty():
            return None
        return self.cards[-1]
    
    def clear(self):
        last_card_id = self.cards[-1]
        self.cards.pop()
        removed_cards = self.cards.copy()
        self.cards = [last_card_id]
        return removed_cards


class PlayerDeck(Deck):
    def __init__(self):
        scr = Card.system_card_range()
        self.cards = [i for i in range(scr[0], scr[1])] # system cards

    def sort(self):
        self.cards.sort()

    def throw_card(self, throw_card_id):
        try:
            return self.pop_card(throw_card_id)
        except PopCardError as err:
            print(err, " Try again.")
            return -1