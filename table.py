from deck import DrawDeck, TableDeck
from player import Player
import json

class Cheater(Exception):
    pass

class Table():
    def __init__(self, players: list):
        self.players = players
        self.drawDeck = DrawDeck()
        self.tableDeck = TableDeck()
        self.turn = 0
        self.isDirectionClockwise = True
        self.startGame()

    def startGame(self):
        for player in self.players:
            for i in range(7):
                card = self.drawDeck.popTop()
                player.deck.receiveCard(card)
    
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
        for player in self.players:
            player.update(self.gameInfo())
        play = self.players[self.turn].handleTurn(self.gameInfo())
        if play not in self.players[self.turn].deck.cards:
            raise(Cheater)
        card = Card(play)
        if card.color == "black":
            self.selectColor()
            if card.type == "+4":
                pass
                
    
    def selectColor(self):
        color = self.players[self.turn].chooseColor()
        self.tableDeck.changeTopCardColor(color)
    
    def changeDirection(self):
        self.isDirectionClockwise = not self.isDirectionClockwise
    
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
    
    def updatePlayers(self):
        pass

if __name__ == "__main__":
    table = Table()