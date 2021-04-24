class Item:
    price = None
    name = None
    description = None
    

    def __init__(self, price, positions=None):
        self.price = price
        self.positions = positions
