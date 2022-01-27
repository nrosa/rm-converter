import json
import xml.etree.ElementTree as et

from src import objects, constants, utils

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
            groups = [constants.chem_groups[x['GROUP_ID']] for x in group_data 
                if x['GROUP_ID'] in constants.chem_groups.keys() and x['CHEMICAL_ID'] == chem['CHEMICAL_ID']
            ]
            # Construct the chemical
            self.chemicals.append(objects.Chemical(
                chem_id = chem['CHEMICAL_ID'],
                name = chem['NAME'],
                cas = chem['CAS'],
                pka = chem['PKA1'] if chem['PKA1'] != '' else None,
                aliases = aliases,
                groups = groups
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
            ) for x in stock_data
        ]

        # Preindex the stock ids
        self.stock_id_idxs = dict()
        for i, stock in enumerate(self.stocks):
            self.stock_id_idxs[stock.id] = i

    def get_stock_by_id(self, stock_id: int):
        return self.stocks[self.stock_id_idxs[stock_id]]



class PhCurveFactory(object):
    def __init__(self, curve_json_path, point_json_path):
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
            recipe_stocks.append(
                objects.RecipeStock(
                    stock = self.stocks_factory.get_stock_by_id(int(stock.attrib['barcode'])),
                    wells = [utils.wellname2id(x.attrib['name']) for x in stock],
                )
            )

        return objects.Recipe(stocks = recipe_stocks)








        


