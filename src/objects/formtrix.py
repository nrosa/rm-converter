from __future__ import annotations
from typing import Optional, List

class TitrationPoint(object):
    def __init__(self, ph, a2b_ratio):
        self.ph = ph
        self.a2b_ration = a2b_ratio


class TitrationTable(object):
    def __init__(self):
        self.points = list()

    def add_point(self, ph, a2b_ratio):
        self.points.append(TitrationPoint(ph, a2b_ratio))


class BufferData(object):
    def __init__(self, pka=None, titration_table=None):
        assert pka is not None or titration_table is not None
        self.pka = pka
        self.titration_table = titration_table


class ConditionIngredient(object):
    def __init__(self,
        conc: float,
        cond_type: str,
        ph : Optional[float],
        stock: Stock,
        high_ph_stock: Optional[Stock],
    ):
        self.conc = conc
        self.type = cond_type
        self.ph = ph
        self.stock = stock
        self.high_ph_stock = high_ph_stock 

    def add_recipe_volume(self, well_volume):
        if self.type == 'Buffer':
            if self.high_ph_stock is not None:
                assert self.stock.ingredient == self.high_ph_stock.ingredient
                if self.stock.ingredient.buffer_data.pka is not None:
                    pka = self.stock.ingredient.buffer_data.pka
                    # Calculate the mix with the henderson hasselbalch equation
                    base_2_acid_ratio = 10 ** (self.ph - pka)

                    total_volume = (well_volume * self.conc) / self.stock.conc

                    self.volume = 
                    self.high_ph_volume = 

        # Easy case
        self.volume = (well_volume * self.conc) / self.stock.conc



class Condition(object):
    def __init__(self):
        self.condition_ingredients = list()

    def add_condition_ingredient(self, condition_ingredient):
        assert isinstance(condition_ingredient, ConditionIngredient)
        self.condition_ingredients.append(condition_ingredient)

    def add_recipe_volume(self, volume):
        total_volume = 0
        for cond_ingred in self.condition_ingredients:
            cond_ingred.add_recipe_volume(volume)
        #     total_volume += cond_ingred.volume
        # print(total_volume)


class Conditions(object):
    def __init__(self):
        self.conditions = list()

    def add_condition(self, condition):
        assert isinstance(condition, Condition)
        self.conditions.append(condition)

    def add_recipe_volume(self, volume):
        for condition in self.conditions:
            condition.add_recipe_volume(volume)


class Stock(object):
    def __init__(self,
        local_id: int,
        conc: float,
        units: str,
        ph: float,
        buffer: bool,
        part_number: str,
        ingredient: Ingredient,
        ):
        self.local_id = local_id
        self.conc = conc
        self.units = units
        self.ph = ph
        self.buffer = buffer
        self.part_number = part_number
        self.ingredient = ingredient


class Ingredient(object):
    def __init__(self, name, buffer_data):
        self.name = name
        self.buffer_data = buffer_data
        self.aliases = list()
        self.stocks = list()

    def add_stock(self, stock):
        assert isinstance(stock, Stock)
        self.stocks.append(stock)

    def add_alias(self, alias):
        assert isinstance(alias, str)
        self.aliases.append(alias)


class Ingredients(object):
    def __init__(self):
        self.ingredients = list()

    def add_ingredient(self, ingredient):
        assert isinstance(ingredient, Ingredient)
        self.ingredients.append(ingredient)

    def get_stock_by_local_id(self, local_id):
        for ingredient in self.ingredients:
            for stock in ingredient.stocks:
                if stock.local_id == local_id:
                    return stock
        return None

class Screen(object):
    def __init__(self, ingredients, conditions):
        self.ingredients = ingredients
        self.conditions = conditions

    def add_recipe_volume(self, volume):
        self.conditions.add_recipe_volume(volume)




