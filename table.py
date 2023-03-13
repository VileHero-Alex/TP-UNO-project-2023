from deck import DrawDeck, TableDeck
from player import Player
import json

class Table():
    def __init__(self, players: list):
        self.players = players
        self.drawDeck = DrawDeck()
        self.tableDeck = TableDeck()
        self.turn = 0
        self.isDirectionClockwise = True
    
    def reshuffle(self):
        if len(self.drawDeck) <= 1:
            cards = self.tableDeck.clear()
            for card in cards:
                self.drawDeck.recieveCard(card)
            self.drawDeck.shuffle()
    
    def draw(self, amount: int, player: Player) -> None:
        for i in range(amount):
            self.reshuffle()
            card = self.drawDeck.popTop()
            player.deck.recieve(card)
    
    def newTurn(self):
        pass
    
    def selectColor(self):
        pass
    
    def changeDirection(self):
        pass
    
    def gameInfo(self):
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
        

if __name__ == "__main__":
    table = Table()