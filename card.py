class Card:
    color_pool = ["red", "yellow", "green", "blue", "black"]
    type_pool = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "skip", "reverse", "+2"]
    type_pool_extra = ["uno", "draw", "red", "yellow", "green", "blue"]

    def __init__(self, id):
        self.id = id
        color, type = self.card_identificator(id)
        self.color = color
        self.type = type

    def card_identificator(id):
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


if __name__ == "__main__":
    for i in range(110):
        print(i, Card(i).type, Card(i).color)