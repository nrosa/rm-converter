from __future__ import annotations
from typing import Optional, List, Set
from lxml import etree
import warnings
from collections import defaultdict

from ..config.constants import SHRTNAME_LEN, WATER, BUFFER, PRECIPITANT
from ..utils import get_shortname_from_lid_name, wellid2name, _is_tacsimate
from .base import BaseXml, ListXml, XmlMixin, VolumeUnitsMixin


class DesignItem:
    # __slots__ = ("chemical", "item_class", "concentration", "units", "ph")

    def __init__(
        self,
        chemical: object,
        item_class: str,
        concentration: float,
        units: str,
        ph: Optional[float],
        one_ph: Optional[bool] = None,
        one_stock: Optional[bool] = None,
    ):
        self.chemical = chemical
        self._item_class = item_class
        self.concentration = concentration
        self.units = units
        self.ph = ph

        # This can be passed if the design item only exists at one ph in the design
        self.one_ph = one_ph
        self.one_stock = one_stock

    def __repr__(self):
        return f'DesignItem({self.chemical.name},{self.concentration},{self.units},{self.ph})'

    # Buffer class fixes
    @property
    def is_buffer(self) -> bool:
        if _is_tacsimate(self.chemical.name):
            return True
        if self.one_stock and self.one_ph:
            return False
        return self._item_class == BUFFER
    
    # Make the item class match the is_buffer property
    @property
    def item_class(self) -> str:
        if self._item_class == BUFFER and not self.is_buffer:
            return PRECIPITANT
        return self._item_class


class DesignWell:
    # __slots__ = ("items")

    def __init__(self, items: List[DesignItem]):
        self.items = items


class Design:
    # __slots__ = ("wells")

    def __init__(self, name):
        # Dict that maps a well id [1,96] to a DesignWell
        self.wells = dict()
        self.name = name

    def add_well(self, well: DesignWell, well_id: int):
        self.wells[well_id] = well

    def get_chems_with_one_ph(self) -> Set[int]:
        chem_ph = defaultdict(set)
        for dw in self.wells.values():
            for di in dw.items:
                if not di.ph is None:
                    chem_ph[di.chemical.id].add(di.ph)
        return set([chem for (chem, phs) in chem_ph.items() if len(phs) == 1])

    def set_one_ph(self) -> None:
        single_chem_ids = self.get_chems_with_one_ph()
        for dw in self.wells.values():
            for di in dw.items:
                di.one_ph = di.chemical.id in single_chem_ids


class Chemical:
    # __slots__ = ("id", "name", "cas", "pka", "aliases",
    #              "shortname")

    def __init__(self,
                 chem_id: Optional[int],
                 name: str,
                 cas: str,
                 pkas: List[float],
                 aliases: List[str],
                 shortname: Optional[str] = None
                 ):
        self.id = chem_id
        self.name = name
        self.cas = cas
        self.pkas = pkas
        self.aliases = aliases
        self.shortname = shortname

        if self.shortname is None:
            shortname = ''
            if len(self.aliases) > 0:
                shortname = sorted(aliases, key=lambda x: len(x))[0]
                if len(shortname) > SHRTNAME_LEN:
                    shortname = shortname[:SHRTNAME_LEN]
            else:
                shortname = name[:SHRTNAME_LEN] if len(
                    name) > SHRTNAME_LEN else name

            self.shortname = shortname

    def __repr__(self):
        return (f'{self.name}')


class PhPoint:
    # __slots__ = ("base_fraction", "acid_fraction", "ph")

    def __init__(self, base_fraction: float, ph: float):
        self.base_fraction = base_fraction
        self.acid_fraction = 100 - base_fraction
        self.ph = ph
        
    def __repr__(self):
        return f'base_frac: {self.base_fraction}, acid_frac: {self.acid_fraction}, ph: {self.ph}'


class PhCurve:
    # __slots__ = ("chem_id", "low_chem_id", "high_chem_id",
    #              "low_ph", "high_ph", "points")

    def __init__(
        self,
        chem: Chemical,
        low_chem: Chemical,
        high_chem: Chemical,
        low_ph: Optional[float],
        high_ph: Optional[float],
        points: List[PhPoint]
    ):
        self.chem = chem
        self.low_chem = low_chem
        self.high_chem = high_chem
        self.low_ph = low_ph
        self.high_ph = high_ph

        self.points = points

        # If either the low ph or high ph are not set then get them from the points
        if self.low_ph is None:
            warnings.warn("Curve has no low pH, using the lowest point in curve")
            self.low_ph = min([point.ph for point in self.points])
        if self.high_ph is None:
            warnings.warn("Curve has no high pH, using the highest point in curve")
            self.high_ph = max([point.ph for point in self.points])

        # Make the highest and lowest ph point equal the high and low ph
        for point in self.points:
            if point.acid_fraction == 0 and point.ph != self.high_ph:
                warnings.warn(
                    f'Warning: Acid fraction 0 pH {point.ph} doesn\'t match curve high pH {self.high_ph}. Overwriting')
                point.ph = self.high_ph
            if point.base_fraction == 0 and point.ph != self.low_ph:
                warnings.warn(
                    f'Warning: Base fraction 0 pH {point.ph} doesn\'t match curve low pH {self.low_ph}. Overwriting')
                point.ph = self.low_ph

# Wellstock


class Stock(VolumeUnitsMixin):
    # __slots__ = ("id", "stock_name", "chem_id", "conc",
    #              "cunits", "ph", "local_id", "short_name",
    #              'wells', 'show_wells')

    def __init__(
        self, *,
        stock_id: Optional[int],
        stock_name: str,
        chem: Chemical,
        conc: float,
        units: str,
        ph: Optional[float],
        viscosity: float,
        volatility: float,
        lid_name: str,
        barcode: str,
        density: Optional[float] = None,
        comments: Optional[str] = None,
        available: bool = True,
    ):
        self.id = stock_id
        self.stock_name = stock_name
        self.chem = chem
        self.density = density
        self.viscosity = viscosity
        self.volatility = volatility
        self.conc = conc
        self.units = units
        self.ph = ph
        self.local_id = None
        self.short_name = get_shortname_from_lid_name(lid_name)
        self.barcode = barcode
        self.comments = comments
        self.wells = []
        self.available = available

        if isinstance(self.chem, int):
            raise Exception('should be chem')
    def add_well(self, well: Well):
        self.wells.append(well)

    @property
    def cunits(self):
        return self.units

    @property
    def pH(self):
        return self.ph

    @property
    def count(self):
        return len(self.wells)

    @property
    def volume(self):
        return sum([x.volume for x in self.wells])
    
    @property
    def name(self):
        return self.chem.name

    def __repr__(self):
        return f'{self.stock_name}, id:{self.id}'


class StockVolCount(Stock, XmlMixin):
    # __slots__ = Stock.__slots__ + BaseXml.__slots__
    def __init__(self, original_stock: Stock):
        super().__init__(
            stock_id=original_stock.id,
            stock_name=original_stock.stock_name,
            chem=original_stock.chem,
            conc=original_stock.conc,
            units=original_stock.cunits,
            ph=original_stock.ph,
            viscosity=original_stock.viscosity,
            volatility=original_stock.volatility,
            lid_name=original_stock.short_name,
            barcode=original_stock.barcode,
            density=original_stock.density,
            comments=original_stock.comments,
        )
        self._xml_name = 'stock'
        self._xml_text = ''
        self._attributes = ['barcode', 'comments', 'conc', 'count', 'cunits',
                            'density', 'name', 'pH', 'viscosity', 'volatility', 'volume', 'vunits']
        self._children = []
        self.wells = list(original_stock.wells)


class StockWells(Stock, XmlMixin):
    def __init__(self, original_stock: Stock):
        super().__init__(
            stock_id=original_stock.id,
            stock_name=original_stock.stock_name,
            chem=original_stock.chem,
            conc=original_stock.conc,
            units=original_stock.cunits,
            ph=original_stock.ph,
            viscosity=original_stock.viscosity,
            volatility=original_stock.volatility,
            lid_name=original_stock.short_name,
            barcode=original_stock.barcode,
            density=original_stock.density,
            comments=original_stock.comments,
        )
        self._xml_name = 'stock'
        self._xml_text = ''
        self._attributes = ['barcode', 'comments', 'conc', 'cunits',
                            'density', 'name', 'pH', 'viscosity', 'volatility']
        self._children = ['wells']
        self.wells = list(original_stock.wells)


class Well(BaseXml, VolumeUnitsMixin):
    # __slots__ = ('volume',)
    def __init__(self, name: str, volume: float):
        super().__init__(name='well', attributes=['name', 'volume', 'vunits'])
        self.name = name
        self.volume = volume


class Wells(BaseXml, VolumeUnitsMixin):
    # __slots__ = ('volume','stocks')
    def __init__(self, volume: float):
        super().__init__(name='wells', attributes=[
            'volume', 'vunits'], children=['stocks'])
        self.volume = volume
        self.stocks = []

    def add_stock(self, stock: StockWells):
        self.stocks.append(stock)


class Plate(BaseXml):
    # __slots__ = ['wells']
    def __init__(self, stocks: List[StockWells], volume: float):
        super().__init__(name='plate', children=['wells'])
        self.wells = Wells(volume)
        for s in stocks:
            self.wells.stocks.append(s)


class SourcePlate(BaseXml):
    # TODO this is missing some attributes and not sure whether they are required: Test
    # barcode, name, plateid, tracking_id
    # __slots__ = ('description', 'stocks','wells', 'name')

    def __init__(self, name: str, description: str, volume: float):
        super().__init__(name='sourceplate', attributes=['description'])
        self.description = description
        self.name = name
        self.volume = volume
        self.stocks = []

    def get_children(self) -> List[XmlMixin]:
        children = []
        children.append(ListXml(
            [StockVolCount(x) for x in self.stocks],
            name='stocks'
        ))
        children.append(
            Plate(stocks=[StockWells(x)
                  for x in self.stocks], volume=self.volume)
        )
        return children

    def get_xml_element(self) -> etree.Element:
        # Automatically wrap this class in the parents
        self_element = etree.Element(
            'job',
            attrib={'name': self.name})
        sourceplates_elem = etree.Element(
            'sourceplates'
        )
        sp_elem = super().get_xml_element()
        sourceplates_elem.append(sp_elem)
        self_element.append(sourceplates_elem)
        return self_element

    def get_stocks_for_well(self, well_id: int) -> List[Stock]:
        well_name = wellid2name(well_id)
        return [x for x in self.stocks if well_name in [y.name for y in x.wells]]

    def add_water(self):
        well_volume_map = {}
        # TODO What to do if a well has no stocks? No water will be added
        for stock in self.stocks:
            for well in stock.wells:
                if well.name not in well_volume_map:
                    well_volume_map[well.name] = 0
                well_volume_map[well.name] += well.volume
        water_stock = self.get_water_stock()
        for k, v in well_volume_map.items():
            if v < self.volume:
                water_stock.add_well(Well(k, self.volume-v))
        self.stocks.append(water_stock)

    def get_water_stock(self):
        water_chem = Chemical(
            int(WATER.barcode),
            WATER.name,
            cas=None,
            pkas=[],
            aliases=[]
        )
        water_stock = Stock(
            stock_id=None,
            stock_name=WATER.name,
            chem=water_chem,
            conc=WATER.conc,
            units=WATER.units,
            ph=None,
            viscosity=WATER.viscosity,
            volatility=None,
            lid_name=None,
            barcode=WATER.barcode,
            density=None,
            comments=WATER.comment,
        )
        return water_stock
