from __future__ import annotations
from typing import Optional, List

from src import constants

class DesignItem(object):
    def __init__(
        self,
        chemical: object,
        item_class: str,
        concentration: float,
        units: str,
        ph: Optional[float]
    ):
        self.chemical = chemical
        self.item_class = item_class
        self.concentration = concentration
        self.units = units
        self.ph = ph

class DesignWell(object):
    def __init__(self, items: List[DesignItem]):
        self.items = items

class Design(object):
    def __init__(self):
        # Dict that maps a well id [1,96] to a DesignWell
        self.wells = dict()

    def add_well(self, well: DesignWell, well_id: int):
        self.wells[well_id] = well


class RecipeStock(object):
    def __init__(self, stock: Stock, wells: List[int]):
        self.stock = stock
        self.wells = wells

class Recipe(object):
    def __init__(self, stocks: List[RecipeStock]):
        self.stocks = stocks

    def get_stocks_for_well(self, well_id: int):
        return [x for x in self.stocks if well_id in x.wells]

# Class for keeping track of the info for a Forumlatrix ingredient
class Ingredient(object):
    def __init__(self, chemical: Chemical):
        self.chemical = chemical

        self.types = set()
        # Set[Tuple[stock_id: int, use_as_buffer: bool]]
        self.stocks = set()

    def add_type(self, ingredient_type: str): 
        self.types.add(ingredient_type)

    def add_stock(self, stock_id: int, use_as_buffer: bool):
        self.stocks.add((stock_id, use_as_buffer))

    def is_buffer(self):
        return constants.BUFFER in self.types


