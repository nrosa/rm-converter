# -*- coding: utf-8 -*-
"""
Created on Tue Oct 29 08:51:07 2024

@author: owe043
"""

import copy


class _ChemicalsFactory:
    def __init__(self, chemicals):
        self.chemicals = chemicals

    def get_chem_by_id(self, chem_id: int):
        return self.chemicals[chem_id]

    def get_chem_by_name(self, chem_name: str):
        for chemical in self.chemicals.values():
            # todo: use string collation
            if chem_name.lower() == chemical.name.lower():
                return chemical
        return None


class _StocksFactory:
    def __init__(self, stocks):

        self.stocks = stocks

    def get_stock_by_id(self, stock_id: int):
        assert isinstance(stock_id, int)
        return copy.deepcopy(self.stocks[stock_id])

    def get_first_stock_by_chemid(self, chem_id: int):
        for stock in self.stocks.values():
            if stock.chem.id == chem_id:
                return copy.deepcopy(stock)
        return None

    def get_stocks_by_chemid(self, chem_id: int):
        return [copy.deepcopy(x) for x in self.stocks.values() if x.chem.id == chem_id]

    def get_stocks_by_chem(self, chem_name: str):
        return [copy.deepcopy(x) for x in self.stocks.values() if x.chem.name == chem_name]


class _PhCurveFactory:
    def __init__(self, curves: dict):

        self.curves = curves

    def get_curve_by_chem_id(self, chem_id: int):
        if chem_id in self.curves:
            return self.curves[chem_id]
        return None

    def get_curve_by_chem_name(self, chem_name: str):
        for curve in self.curves.values():
            # todo: use string collation
            if chem_name.lower() == curve.chem.name.lower():
                return curve
        return None

    def is_chem_curve(self, chem_id: int) -> bool:
        return chem_id in self.curves
