from __future__ import annotations

import json
from lxml import etree

from ..config import constants
from ..exceptions import ChemNotFoundError
from ..objects import xtaltrak as xt_objects
from ..factories.bases import _ChemicalsFactory, _StocksFactory, _PhCurveFactory


class ChemicalsFactory(_ChemicalsFactory):
    def __init__(self, chem_json_path, alias_json_path):
        with open(chem_json_path) as fp:
            chem_data = json.load(fp)
        with open(alias_json_path) as fp:
            alias_data = json.load(fp)

        aliases = {chem['CHEMICAL_ID']: [] for chem in chem_data}
        for x in alias_data:
            aliases[x['CHEMICAL_ID']].append(x['CHEM_ALIAS'])

        self.name_index = {}

        # Load all the chemicals
        chemicals = dict()
        for chem in chem_data:

            chem_id = chem['CHEMICAL_ID']

            # Construct the chemical
            chemicals[chem_id] = xt_objects.Chemical(
                chem_id=chem_id,
                name=chem['NAME'],
                cas=chem['CAS'],
                pkas=[chem[x] for x in ['PKA1', 'PKA2', 'PKA3'] if chem[x]],
                aliases=aliases[chem_id]
            )

            # Create a name index
            self.name_index[chem['NAME'].lower()] = chem_id
            for alias in aliases[chem_id]:
                self.name_index[alias.lower()] = chem_id

        super().__init__(chemicals)

    def get_chem_by_name(self, chem_name: str):
        chem_name = chem_name.lower()
        if chem_name in self.name_index:
            return self.get_chem_by_id(self.name_index[chem_name])
        return super().get_chem_by_name(chem_name=chem_name)


class StocksFactory(_StocksFactory):
    def __init__(self, stock_json_path, chems_f: _ChemicalsFactory):
        with open(stock_json_path) as fp:
            stock_data = json.load(fp)
        stocks = {
            x['STOCK_ID']: xt_objects.Stock(
                stock_id=x['STOCK_ID'],
                stock_name=x['STOCK_NAME'],
                chem=chems_f.get_chem_by_id(x['CHEMICAL_ID']),
                conc=x['STOCK_CONC'],
                units=x['STOCK_UNITS'],
                ph=x['STOCK_PH'],
                volatility=x['STOCK_VOLATILITY'],
                viscosity=x['STOCK_VISCOSITY'],
                lid_name=x['STOCK_LIDS'],
                barcode=x['STOCK_BARCODE']
            ) for x in stock_data
        }

        super().__init__(stocks)


class PhCurveFactory(_PhCurveFactory):
    def __init__(self, curve_json_path: str, point_json_path: str, chems_f: _ChemicalsFactory):
        with open(curve_json_path) as fp:
            curve_data = json.load(fp)
        with open(point_json_path) as fp:
            point_data = json.load(fp)

        # First find all the points
        points = dict()
        for curve in curve_data:
            curve_id = curve['PK_PH_CURVE_ID']
            points[curve_id] = []

        for x in point_data:
            curve_id = x['FK_PH_CURVE_ID']
            points[curve_id].append(xt_objects.PhPoint(
                base_fraction=x['HIGH_PH_FRACTION_X'],
                ph=x['RESULT_PH_Y']
            ))

        curves = dict()
        for curve in curve_data:
            curve_id = curve['PK_PH_CURVE_ID']
            assert isinstance(curve_id, int)

            chem = chems_f.get_chem_by_id(curve['FK_CHEMICAL_ID'])
            # assert isinstance(chem_id, int)

            curves[chem.id] = xt_objects.PhCurve(
                chem=chem,
                low_chem=chems_f.get_chem_by_id(curve['LOW_SOURCE_ID']),
                high_chem=chems_f.get_chem_by_id(curve['HIGH_SOURCE_ID']),
                low_ph=curve['LOW_PH'],
                high_ph=curve['HIGH_PH'],
                points=points[curve_id],
            )

        super().__init__(curves)


class DesignFactory(object):
    def __init__(self, chem_factory: ChemicalsFactory):
        self.chem_factory = chem_factory

    def get_design_from_xml_object(self, xml_root) -> xt_objects.Design:
        rd_xml = xml_root.find('reservoir_design')

        design = xt_objects.Design(name=rd_xml.attrib['name'])

        for well in rd_xml.findall('well'):
            design_items = list()
            for item in well:
                # Find the chemical
                chem = self.chem_factory.get_chem_by_name(
                    item.attrib['name'])
                if chem is None:
                    # If the chemical cant be found by name then try to use the barcode
                    if 'barcode' in item.attrib:
                        chem = self.chem_factory.get_chem_by_id(
                            int(item.attrib['barcode'])
                        )
                    if chem is None:
                        raise ChemNotFoundError(
                            f'Cant find chemical {item.attrib["name"]}')
                design_items.append(
                    xt_objects.DesignItem(
                        chemical=chem,
                        item_class=item.attrib['class'],
                        concentration=float(item.attrib['conc']),
                        units=item.attrib['units'],
                        ph=float(
                            item.attrib['ph']) if item.attrib['ph'] != '' else None
                    )
                )
            design.add_well(xt_objects.DesignWell(
                items=design_items), int(well.attrib['number']))

        return design

    def get_design_from_xml_file(self, path):
        return self.get_design_from_xml_object(etree.parse(path).getroot())

    def get_design_from_xml_str(self, design_xml: str):
        return self.get_design_from_xml_object(etree.fromstring(design_xml))


class RecipeFactory(object):
    def __init__(self, stocks_factory):
        self.stocks_factory = stocks_factory

    def get_recipe_from_xml_object(self, xml_root) -> xt_objects.SourcePlate:
        name = xml_root.attrib['name']

        sp_xml = xml_root.find('sourceplates').find('sourceplate')
        wells_xml = sp_xml.find('plate').find('wells')
        volume = float(wells_xml.attrib['volume'])
        vunits = wells_xml.attrib['vunits']

        # TODO convert volume units
        if vunits != constants.VUNITS:
            raise Exception(f'Volume units "{vunits}" is not recognised.')

        sp = xt_objects.SourcePlate(
            name=name,
            description=sp_xml.attrib['description'],
            volume=volume
        )

        for stock_xml in sp_xml.find('plate').find('wells'):
            if len(stock_xml.attrib['barcode']) == 0:
                raise Exception(
                    f"Empty barcode for {stock_xml.attrib['name']}")
            count = 0
            lengths = []
            if stock_xml.attrib['barcode'] != constants.WATER.barcode:
                stock = self.stocks_factory.get_stock_by_id(
                    int(stock_xml.attrib['barcode']))
                if stock is None:
                    raise Exception(
                        f"Cant find stock {stock_xml.attrib['name']}")
                for well in stock_xml:
                    if well.attrib['vunits'] != constants.VUNITS:
                        raise Exception(f'vunits must be {constants.VUNITS}')
                    stock.add_well(xt_objects.Well(
                        name=well.attrib['name'],
                        volume=float(well.attrib['volume'])
                    ))
                    lengths.append(len(stock.wells))
                    count += 1
                sp.stocks.append(
                    stock
                )

        return sp
