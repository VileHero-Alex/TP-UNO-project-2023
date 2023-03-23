class Card:
    color_pool = ["red", "yellow", "green", "blue", "black"]
    type_pool = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "skip", "reverse", "+2", "choose", "+4"]
    type_pool_extra = ["uno", "draw", "red", "yellow", "green", "blue", "challenge", "accept", "1", "2", "3", "4"]
    system_cards_range = (108, 120)

    def __init__(self, card_id: int):
        if card_id >= Card.system_cards_range[1]:
            raise InputError(f"Card with that ID ({card_id}) doesn't exist")
        self.id = card_id
        color, type = self.card_identificator(card_id)
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


if __name__ == "__main__":
    print(Card.color_pool)