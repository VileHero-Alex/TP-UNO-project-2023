import random
from card import Card
from errors import PopCardError


class Deck:
    def __init__(self, cards):
        self.cards = cards

    def __len__(self):
        return len(self.cards)
    
    def popCard(self, pop_card_id):
        try:
            self.cards.remove(pop_card_id)
            return pop_card_id
        except:
            raise PopCardError("illegal move: there is no card that you are looking for!")

    def receiveCard(self, receive_card_id):
        self.cards.append(receive_card_id)


class DrawDeck(Deck):
    def shuffle(self):
        random.shuffle(self.cards)
    
    def popTop(self):
        received_card_id = self.popCard(self.cards[0])
        return received_card_id

    def isEmpty(self):
        return len(self.cards) == 0

class TableDeck(Deck):
    def showLast(self):
        return self.cards[-1]
    
    def clear(self):
        last_card_id = self.cards[-1]
        self.cards.pop()
        removed_cards = self.cards.copy()
        self.cards = [last_card_id]
        return removed_cards


class PlayerDeck(Deck):
    def sort(self):
        self.cards.sort()

    def throwCard(self, throw_card_id):
        try:
            return self.popCard(throw_card_id)
        except PopCardError as err:
            print(err, " Try again.")
            return -1