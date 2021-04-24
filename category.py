from PIL import Image
class Category:
    price = None
    positions =  None

    def __init__(self, price, positions=None):
        self.price = price
        self.positions = positions
