from __future__ import annotations
from typing import Optional, List

from src.objects.xml import BaseXmlObject2

class Stock(BaseXmlObject2):
    def __init__(
        self,
        barcode,
        comments,
        conc,
        count,
        cunits,
        density,
        name,
        ph,
        viscosity,
        volatility,
        volume,
        vunits,
    ):

        self.barcode = barcode
        self.comments = comments
        self.conc = conc
        self.count = count
        self.cunits = cunits
        self.density = density
        self.name = name
        self.ph = ph
        self.viscosity = viscosity
        self.volatility = volatility
        self.volume = volume
        self.vunits = vunits


    def get_attrib(self):
        attrib = {
            'barcode' : str(self.barcode),
            'comments' : self.comments,
            'conc' : str(self.conc),
            'count' : str(self.count),
            'cunits' : self.cunits,
            'density' : str(self.density),
            'name' : self.name,
            'pH' : str(self.ph),
            'viscosity' : str(self.viscosity),
            'volatility' : str(self.volatility),
            'volume' : str(self.volume),
            'vunits' : self.vunits

        }
        return attrib

    def get_name(self):
        return 'stock'


class Stocks(BaseXmlObject2):
    def __init__(self):
        self.stocks = list()

    def add_stock(self, stock):
        assert isinstance(stock, Stock)
        self.stocks.append(stock)

    def get_name(self):
        return 'stocks'

    def get_children(self):
        return self.stocks


class SourcePlate(BaseXmlObject2):
    def __init__(self, description, stocks, plate):
        self.description = description
        assert isinstance(stocks, Stocks)
        self.stocks = stocks
        assert isinstance(plate, Plate)
        self.plate = plate
        super().__init__(name='sourceplate', attrib=attrib)

    def get_name(self):
        return 'sourceplate'

    def get_attrib(self):
        return {
            'barcode' : '',
            'description' : self.description,
            'name' : '',
            'plateid' : '',
            'tracking_id' : '',
        }

    def get_children(self):
        return [self.stocks, self.plate]


class SourcePlates(BaseXmlObject2):
    def __init__(self):
        self.sourceplates = list()

    def add_sourceplate(self, sourceplate):
        assert isinstance(sourceplate, SourcePlate)
        self.sourceplates.append(sourceplate)

    def get_name(self):
        return 'sourceplates'

    def get_children(self):
        return self.sourceplates
        

class Job(BaseXmlObject2):
    def __init__(self, name, sourceplates):
        assert isinstance(sourceplates, SourcePlates)
        self.sourceplates = sourceplates
        self.name = name

    def get_name(self):
        return 'job'

    def get_attrib(self):
        return {
            'CrystalTrak_id' : 'TBD',
            'Job_id' : '1.0.0.0',
            'crystaltrak_version' : '-',
            'name' : self.name,
            'schema_version' : '1.0.0.2',
        }

    def get_children(self):
        return [self.sourceplates]


class Plate(BaseXmlObject2):
    def __init__(self, wells):
        assert isinstance(wells, Wells)
        self.wells = wells

    def get_name(self):
        return 'plate'

    def get_children(self):
        return [self.wells]


class Wells(BaseXmlObject2):
    def __init__(self, volume):
        self.volume = volume
        self.stocks = list()

    def add_stock(self, stock):
        assert isinstance(stock, WellStock)
        self.stocks.append(stock)

    def get_name(self):
        return 'wells'

    def get_attrib(self):
        return {'volume' : str(self.volume), 'vunits' : 'ul'}

    def get_children(self):
        return self.stocks


class WellStock(BaseXmlObject2):
    def __init__(self,
        barcode,
        comments,
        conc,
        cunits,
        density,
        name,
        ph,
        viscosity,
        volatility
    ):
        self.barcode
        self.comments
        self.conc
        self.self.cunits
        self.density
        self.name
        self.ph
        self.viscosity
        self.volatility

        self.wells = list()

    def add_well(self, well):
        assert isinstance(well, Well)
        self.wells.append(well)

    def get_name(self):
        return 'stock'

    def get_attrib(self):
        return {
            'barcode' : str(self.barcode),
            'comments' : self.comments,
            'conc' : str(self.conc),
            'cunits' : self.cunits,
            'density' : str(self.density),
            'name' : self.name,
            'pH' : str(self.ph),
            'viscosity' : str(self.viscosity),
            'volatility' : str(self.volatility),
        }

    def get_children(self):
        return self.wells


class Well(BaseXmlObject2):
    def __init__(self, well_name, volume, vunits):
        self.well_name = well_name
        self.volume = volume
        self.vunits = vunits

    def get_name(self):
        return 'well'

    def get_attrib(self):
        return {
            'name' : self.well_name,
            'volume' : str(self.volume),
            'vunits' : self.vunits,
        }
        