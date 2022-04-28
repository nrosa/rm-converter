from __future__ import annotations
from typing import Optional, List

import warnings

from src.constants import SHRTNAME_LEN

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

class Chemical(object):
    def __init__(self,
        chem_id: int,
        name: str,
        cas: str,
        pka: Optional[float],
        aliases: List[str],
        groups: List[str],
        pka_warn: bool,
    ):
        self.id = chem_id
        self.name = name 
        self.cas = cas
        self.pka = pka
        self.aliases = aliases
        self.groups = groups

        self.pka_warn = False

        shortname = ''
        if len(self.aliases) > 0:
            shortname = sorted(aliases, key=lambda x: len(x))[0]
            if len(shortname) > SHRTNAME_LEN:
                shortname = shortname[:SHRTNAME_LEN]
        else:
            shortname = name[:SHRTNAME_LEN] if len(name) > SHRTNAME_LEN else name

        self.shortname = shortname


class PhPoint(object):
    def __init__(self, base_fraction: float, ph: float):
        self.base_fraction = base_fraction
        self.acid_fraction = 100 - base_fraction
        self.ph = ph

class PhCurve(object):
    def __init__(
        self,
        chem_id: int,
        low_chem_id: int,
        high_chem_id: int,
        low_ph: float,
        high_ph: float,
        points: List[PhPoint]
    ):
        self.chem_id = chem_id
        self.low_chem_id = low_chem_id
        self.high_chem_id = high_chem_id
        self.low_ph = low_ph
        self.high_ph = high_ph

        self.points = points

        # Make the highest and lowest ph point equal the high and low ph
        for point in self.points:
            if point.acid_fraction == 0:
                if point.ph != self.high_ph:
                    warnings.warn(f'Warning: Acid fraction 0 pH {point.ph} doesn\'t match curve high pH {self.high_ph}. Overwriting')
                    point.ph = self.high_ph
            if point.base_fraction == 0:
                if point.ph != self.low_ph:
                    warnings.warn(f'Warning: Base fraction 0 pH {point.ph} doesn\'t match curve low pH {self.low_ph}. Overwriting')
                    point.ph = self.low_ph



class Stock(object):
    def __init__(
        self,
        stock_id: int,
        chem_id: int,
        conc: float,
        units: str,
        ph: Optional[float],
        lid_name: str,
    ):
        self.id = stock_id
        self.chem_id = chem_id
        self.conc = conc
        self.units = units
        self.ph = ph
        self.local_id = None
        self.lid_name = lid_name
