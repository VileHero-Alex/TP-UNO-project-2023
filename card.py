class Card:
    def __init__(self, id):
        self.id = id
        color, type = self.cardIdentificator(id)
        self.color = color
        self.type = type

    def cardIdentificator(self, id):
        color_pool = ["red", "yellow", "green", "blue", "black"]
        type_pool = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "skip", "reverse", "+2", "choose", "+4"]
        
        color = color_pool[id // 25]
        
        if id % 25 == 0 and id != 100:
            type = "0"
        elif 104 <= id <= 107:
            type = "+4"
        elif 100 <= id <= 103:
            type = "choose"
        else:
            type = type_pool[(id % 25 + 1) // 2] 

        return (color, type)