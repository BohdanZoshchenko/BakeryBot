class Item:
    price = None
    name = None
    description = None
    photo = None

    def __init__(self, price = None, name = None, description = None, photo = None):
        self.price = price
        self.name = name
        self.description = description
        self.photo = photo
        ####commit it