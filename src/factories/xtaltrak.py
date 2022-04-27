from __future__ import annotations
from typing import Optional

import json
import xml.etree.ElementTree as et

from src import constants, objects, utils


class ChemicalsFactory(object):
    def __init__(self, chem_json_path, alias_json_path, group_json_path):
        with open(chem_json_path) as fp:
            chem_data = json.load(fp)
        with open(alias_json_path) as fp:
            alias_data = json.load(fp)
        with open(group_json_path) as fp:
            group_data = json.load(fp)

        # Load all the chemicals
        self.chemicals = list()
        for chem in chem_data:
            # First find all the aliases
            aliases = [x['CHEM_ALIAS'] for x in alias_data if x['CHEMICAL_ID'] == chem['CHEMICAL_ID']]
            # Second find the chem groups
            groups = [constants.CHEM_GROUPS[x['GROUP_ID']] for x in group_data 
                if x['GROUP_ID'] in constants.CHEM_GROUPS.keys() and x['CHEMICAL_ID'] == chem['CHEMICAL_ID']
            ]

            # Construct the chemical
            self.chemicals.append(objects.Chemical(
                chem_id = chem['CHEMICAL_ID'],
                name = chem['NAME'],
                cas = chem['CAS'],
                pka = chem['PKA1'] if chem['PKA1'] != '' else None,
                aliases = aliases,
                groups = groups,
                pka_warn = chem['PKA2'] is not None or chem['PKA3'] is not None
            ))
                

        # Pre index the chemical id's
        self.chem_id_idxs = dict()
        for i, chem in enumerate(self.chemicals):
            self.chem_id_idxs[chem.id] = i

    def get_chem_by_id(self, chem_id: int):
        return self.chemicals[self.chem_id_idxs[chem_id]]

    def get_chem_by_name(self, chem_name: str):
        for chemical in self.chemicals:
            if chem_name.lower() == chemical.name.lower():
                return chemical

    def get_all_chemicals(self):
        return self.chemicals


class StocksFactory(object):
    def __init__(self, stock_json_path):
        with open(stock_json_path) as fp:
            stock_data = json.load(fp)

        self.stocks = [
            objects.Stock(
                stock_id = x['STOCK_ID'],
                chem_id = x['CHEMICAL_ID'],
                conc = x['STOCK_CONC'],
                units = x['STOCK_UNITS'],
                ph = x['STOCK_PH'],
                lid_name = x['STOCK_LIDS']
            ) for x in stock_data
        ]

        # Preindex the stock ids
        self.stock_id_idxs = dict()
        for i, stock in enumerate(self.stocks):
            self.stock_id_idxs[stock.id] = i

    def get_stock_by_id(self, stock_id: int):
        assert isinstance(stock_id, int)
        return self.stocks[self.stock_id_idxs[stock_id]]

    def get_stock_by_chem_conc_ph(self, chem_id: int, conc: float, ph: float) -> Optional[objects.Stock]:
        for stock in self.stocks:
            if stock.chem_id == chem_id and stock.conc == conc and stock.ph == ph:
                return stock
        return None

    def get_stock_by_name(self, name: str) -> Optional[objects.Stock]:
        for stock in self.stocks:
            if stock.name == name:
                return stock
        return None

    def get_first_stock_by_chemid(self, chem_id: int):
        for stock in self.stocks:
            if stock.chem_id == chem_id:
                return stock
        return None



class PhCurveFactory(object):
    def __init__(self, curve_json_path: str, point_json_path: str, stocks_factory: StocksFactory):
        with open(curve_json_path) as fp:
            curve_data = json.load(fp)
        with open(point_json_path) as fp:
            point_data = json.load(fp)

        self.curves = list()
        for curve in curve_data:
            # First find all the points
            points = [
                objects.PhPoint(
                    base_fraction=x['HIGH_PH_FRACTION_X'],
                    ph = x['RESULT_PH_Y']
                ) for x in point_data if x['FK_PH_CURVE_ID'] == curve['PK_PH_CURVE_ID']
            ]

            self.curves.append(objects.PhCurve(
                chem_id = curve['FK_CHEMICAL_ID'],
                low_chem_id = curve['LOW_SOURCE_ID'],
                high_chem_id = curve['HIGH_SOURCE_ID'],
                low_ph = curve['LOW_PH'],
                high_ph = curve['HIGH_PH'],
                points = points,
            ))

        # Preindex the chem ids
        self.chem_id_idxs = dict()
        for i, curve in enumerate(self.curves):
            self.chem_id_idxs[curve.chem_id] = i

    def get_curve_by_chem_id(self, chem_id: int):
        return self.curves[self.chem_id_idxs[chem_id]]

    def is_chem_curve(self, chem_id: int) -> bool:
        return chem_id in [x.chem_id for x in self.curves]



class DesignFactory(object):
    def __init__(self, chem_factory: ChemicalsFactory):
        self.chem_factory = chem_factory

    def get_design_from_xml(self, design_xml_path: str):
        xml_tree = et.parse(design_xml_path)
        xml_root = xml_tree.getroot()

        design = objects.Design()

        for well in xml_root.find('reservoir_design').findall('well'):
            design_items = list()
            for item in well:
                design_items.append(
                    objects.DesignItem(
                        chemical = self.chem_factory.get_chem_by_name(item.attrib['name']),
                        item_class = item.attrib['class'],
                        concentration = float(item.attrib['conc']),
                        units = item.attrib['units'],
                        ph = float(item.attrib['ph']) if item.attrib['ph'] != '' else None
                    )
                )
            design.add_well(objects.DesignWell(items = design_items), int(well.attrib['number']))

        return design


class RecipeFactory(object):
    def __init__(self, stocks_factory):
        self.stocks_factory = stocks_factory

    def get_recipe_from_xml(self, recipe_xml_path: str):
        xml_tree = et.parse(recipe_xml_path)
        xml_root = xml_tree.getroot()

        recipe_stocks = list()
        for stock in xml_root.find('sourceplates').find('sourceplate').find('plate').find('wells'):
            if stock.attrib['barcode'] != constants.WATER_BARCODE:
                recipe_stocks.append(
                    objects.RecipeStock(
                        stock = self.stocks_factory.get_stock_by_id(int(stock.attrib['barcode'])),
                        wells = [utils.wellname2id(x.attrib['name']) for x in stock],
                    )
                )

        return objects.Recipe(stocks = recipe_stocks)