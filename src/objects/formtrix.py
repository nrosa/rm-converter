from __future__ import annotations
from typing import Optional, List


class ConditionIngredient(object):
    def __init__(self, conc: float, cond_type: str, local_id: int):
        self.conc = conc
        self.type = cond_type
        self.local_id = local_id

class Condition(object):
    def __init__(self):
        self.condition_ingredients = list()

    def add_condition_ingredient(self, condition_ingredient):
        assert isinstance(condition_ingredient, ConditionIngredient)
        self.condition_ingredients.append(condition_ingredient)

class Conditions(object):
    def __init__(self):
        self.conditions = list()

    def add_condition(self, condition):
        assert isinstance(condition, Condition)
        self.conditions.append(condition)

class Stock(object):
    def __init__(self, local_id: int, units: str, buffer: bool):
        self.local_id = local_id
        self.units = units
        self.buffer = buffer

class Ingredient(object):
    def __init__(self, name):
        self.name = name
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

class Screen(object):
    def __init__(self, ingredients, conditions):
        self.ingredients = ingredients
        self.conditions = conditions




