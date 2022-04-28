from __future__ import annotations
from typing import Optional, List

from src import constants

# Class for keeping track of the info for a Forumlatrix ingredient
class IngredientTracker(object):
    def __init__(self):
        # self.chemical = chemical

        self.types = set()
        # Set[Tuple[stock_id: int, use_as_buffer: bool]]
        self.stocks = set()

    def add_type(self, ingredient_type: str): 
        self.types.add(ingredient_type)

    def add_stock(self, stock_id: int, use_as_buffer: bool):
        self.stocks.add((stock_id, use_as_buffer))

    def is_buffer(self):
        return constants.BUFFER in self.types