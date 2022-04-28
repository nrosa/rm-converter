from __future__ import annotations
from typing import Optional, List

from src.objects.xml import BaseXmlObject

class StockXml(BaseXmlObject):
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
        attrib = {
            'barcode' : str(barcode),
            'comments' : comments,
            'conc' : str(conc),
            'count' : str(count),
            'cunits' : cunits,
            'density' : str(density),
            'name' : name,
            'pH' : str(ph),
            'viscosity' : str(viscosity),
            'volatility' : str(volatility),
            'volume' : str(volume),
            'vunits' : vunits

        }
        super().__init__(name='stock', attrib = attrib)


class StocksXml(BaseXmlObject);
    def __init__(self):
        super().__init__(name='stocks')
        # TODO Add stock

class SourcePlateXml(BaseXmlObject):
    def __init__(self, description):
        attrib = {
            'barcode' : '',
            'description' : description,
            'name' : '',
            'plateid' : '',
            'tracking_id' : '',
        }
        super().__init__(name='sourceplate', attrib=attrib)

class SourcePlatesXml(BaseXmlObject):
    def __init__(self):
        super().__init__(name='sourceplates')

class JobXml(BaseXmlObject):
    def __init__(self, name):
        attrib = {
            'CrystalTrak_id' : 'TBD',
            'Job_id' : '1.0.0.0',
            'crystaltrak_version' : '-',
            'name' : name,
            'schema_version' : '1.0.0.2',
        }
        super().__init__(name='job', attrib=attrib)

class PlateXml(BaseXmlObject):
    def __init__(self):
        super().__init__(name='plate')


class WellsXml(BaseXmlObject):
    def __init__(self, volume):
        attrib = {'volume' : str(volume), 'vunits' : 'ul'}
        super().__init__(name='wells')

class WellStockXml(BaseXmlObject):
    def __init__(self, barcode, comments, conc, cunits, density, name, ph, viscosity, volatility):
        attrib = {
            'barcode' : str(barcode),
            'comments' : comments,
            'conc' : str(conc),
            'cunits' : cunits,
            'density' : str(density),
            'name' : name,
            'pH' : str(ph),
            'viscosity' : str(viscosity),
            'volatility' : str(volatility),
        }
        super().__init__(name='stock', attrib = attrib)

class WellXml(BaseXmlObject):
    def __init__(self, well_name, volume, vunits):
        attrib = {
            'name' : well_name,
            'volume' : str(volume),
            'vunits' : vunits,
        }
        super().__init__(name='well', attrib=attrib)
        