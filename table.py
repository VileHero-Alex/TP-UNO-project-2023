from deck import DrawDeck, TableDeck
from player import Player
import json

class Cheater(Exception):
    pass

class 

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
        self.turn = self.nextTurn()
    
    def gameUpdate(self):
        self.updatePlayers()
        play = self.players[self.turn].handleTurn(self.gameInfo())
        if play not in self.players[self.turn].deck.cards:
            raise(Cheater)
        card = Card(play)
        next_player = self.nextTurn()
        if card.color == "black":
            self.selectColor()
            if card.type == "+4":
                self.draw(4, self.players[next_player])
        elif card.color == self.tableDeck.topCard.color or card.type == self.tableDeck.topCard.type:
            self.players[self.turn].deck.popCard(card.id)
            self.tableDeck.receiveCard(card)
            if card.type == "change":
                self.changeDirection()
            elif card.type == "+2":
                self.draw(2, self.players[next_player])
            elif card.type == "skip":
                self.turn = self.nextTurn()
        elif card.id == 108:
            new_card = self.tableDeck.popTop()
            self.player[self.turn].deck.receiveCard(new_card)
        self.turn = self.nextTurn()

    
    def selectColor(self):
        color = self.players[self.turn].chooseColor()
        self.tableDeck.changeTopCardColor(color)
        self.updatePlayers()
    
    def changeDirection(self):
        self.isDirectionClockwise = not self.isDirectionClockwise
    
    def nextTurn(self):
        if self.isDirectionClockwise:
            next_player = (self.turn + 1) % len(self.players)
        else:
            next_player = (self.turn + len(self.players) - 1) % len(self.players)
        return next_player

    
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
        for player in self.players:
            player.update(self.gameInfo())

if __name__ == "__main__":
    table = Table()