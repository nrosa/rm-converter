from __future__ import annotations
from typing import Optional, List
import xml.etree.ElementTree as et

####################################################################################################
# C3 Objects
####################################################################################################

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
            if len(shortname) > 8:
                shortname = shortname[:8]
        else:
            shortname = name[:8] if len(name) > 8 else name

        self.shortname = shortname


class PhPoint(object):
    def __init__(self, base_fraction: float, ph: float):
        self.base_fraction = base_fraction
        self.ph = ph

class PhCurve(object):
    def __init__(self, chem_id: int, low_chem_id:int, high_chem_id:int, points: List[PhPoint]):
        self.chem_id = chem_id
        self.low_chem_id = low_chem_id
        self.high_chem_id = high_chem_id
        self.points = points

class Stock(object):
    def __init__(self, stock_id: int, chem_id: int, conc: float, units: str, ph: Optional[float]):
        self.id = stock_id
        self.chem_id = chem_id
        self.conc = conc
        self.units = units
        self.ph = ph
        self.local_id = None


class DesignItem(object):
    def __init__(
        self,
        chemical: Chemical,
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




####################################################################################################
# Rockmaker Xml Objects
####################################################################################################

class BaseXmlObject(object):
    def __init__(self, name: str, text: str = ''):
        self.text = text
        self.name = name
        self.children = []

    def add_child(self, child: BaseXmlObject):
        assert isinstance(child, BaseXmlObject)
        self.children.append(child)

    def get_xml_element(self) -> et.Element:
        self_element = et.Element(self.name)
        self_element.text = self.text

        for child in self.children:
            self_element.append(child.get_xml_element())

        return self_element



class ConditionsXml(BaseXmlObject):
    def __init__(self):
        super().__init__(name='conditions')

class ConditionXml(BaseXmlObject):
    def __init__(self):
        super().__init__(name='condition')

    def add_ingredient(self, ingredient: ConditionIngredientXml):
        self.add_child(ingredient)

class ConditionIngredientXml(BaseXmlObject):
    def __init__(
        self,
        item_class:str,
        concentration: float,
        ph: Optional[float],
        local_id: int,
        high_local_id: Optional[int]
    ):
        super().__init__(name='conditionIngredient')
        self.add_child(ConcentrationXml(concentration))
        if ph is not None:
            self.add_child(PhXml(ph))
        self.add_child(TypeXml(item_class))
        self.add_child(LocalIdXml(local_id))
        if high_local_id is not None:
            self.add_child(HighPhLocalIdXml(high_local_id))


class TypeXml(BaseXmlObject):
    def __init__(self, condition_type: str):
        super().__init__(name='type', text=condition_type)

class TypesXml(BaseXmlObject):
    def __init__(self, types: List[str]):
        super().__init__(name='types')
        for condition_type in types:
            self.add_child(TypeXml(condition_type))

class ConcentrationXml(BaseXmlObject):
    def __init__(self, concentration: float):
        super().__init__(name='concentration', text=str(concentration))

class PhXml(BaseXmlObject):
    def __init__(self, ph: float):
        super().__init__(name='pH', text=str(ph))

class LocalIdXml(BaseXmlObject):
    def __init__(self, local_id: int):
        super().__init__(name='stockLocalID', text=str(local_id))

class HighPhLocalIdXml(BaseXmlObject):
    def __init__(self, local_id: int):
        super().__init__(name='highPHStockLocalID', text=str(local_id))

class IngredientsXml(BaseXmlObject):
    def __init__(self):
        super().__init__(name='ingredients')

class IngredientXml(BaseXmlObject):
    def __init__(
        self,
        name: str,
        cas_number: str,
        shortname: str,
        aliases : List[str],
        types: List[str],
        buffer_data: Optional[BufferDataXml],
        stocks : StocksXml,
    ):
        super().__init__(name='ingredient')
        self.add_child(stocks)
        self.add_child(AliasesXml(aliases))
        self.add_child(TypesXml(types))
        if buffer_data is not None:
            self.add_child(buffer_data)
        self.add_child(CasNumbersXml(cas_number))
        self.add_child(NameXml(name))
        self.add_child(ShortNameXml(shortname))

class ShortNameXml(BaseXmlObject):
    def __init__(self, shortname: str):
        super().__init__(name='shortName', text=shortname)    

class NameXml(BaseXmlObject):
    def __init__(self, name: str):
        super().__init__(name='name', text=name)

class AliasesXml(BaseXmlObject):
    def __init__(self, aliases: List[str]):
        super().__init__(name='aliases')
        for alias in aliases:
            self.add_child(AliasXml(alias))

class AliasXml(BaseXmlObject):
    def __init__(self, alias: str):
        super().__init__(name='alias', text=alias)

class CasNumbersXml(BaseXmlObject):
    def __init__(self, cas_number):
        super().__init__(name='casNumbers')
        self.add_child(CasNumberXml(cas_number))

class CasNumberXml(BaseXmlObject):
    def __init__(self, cas_number: str):
        super().__init__(name='casNumber', text=cas_number)

class BufferDataXml(BaseXmlObject):
    def __init__(self, pka : Optional[float] = None, titration_points: Optional[List[float, float]] = None):
        super().__init__(name='bufferData')
        if pka is not None:
            self.add_child(PkaXml(pka))
        if titration_points is not None:
            self.add_child(TitrationTableXml(titration_points))

class PkaXml(BaseXmlObject):
    def __init__(self, pka: float):
        super().__init__(name='pKa', text=str(pka))

class TitrationTableXml(BaseXmlObject):
    def __init__(self, points: List[float, float]):
        super().__init__(name='titrationTable')
        for point in points:
            self.add_child(TitrationPointXml(*point))

class TitrationPointXml(BaseXmlObject):
    def __init__(self, ph: float, a2b_ratio: float):
        super().__init__(name='titrationPoint')
        self.add_child(PhXml(ph))
        self.add_child(AcidToBaseRatioXml(a2b_ratio))

class AcidToBaseRatioXml(BaseXmlObject):
    def __init__(self, a2b_ratio: float):
        super().__init__(name='acidToBaseRatio', text=str(a2b_ratio))

class StocksXml(BaseXmlObject):
    def __init__(self):
        super().__init__(name='stocks')

    def add_stock(self, stock : StockXml):
        self.add_child(stock)

class StockXml(BaseXmlObject):
    def __init__(
        self,
        local_id: int,
        concentration: float,
        units: str,
        use_as_buffer: bool,
        ph: Optional[float],
    ):
        super().__init__(name='stock')
        self.add_child(StockLocalIdXml(local_id))
        self.add_child(StockConcentrationXml(concentration))
        self.add_child(UnitsXml(units))    
        if ph is not None:
            self.add_child(PhXml(ph))
        self.add_child(UseAsBufferXml(use_as_buffer))
        self.add_child(LowConcentrationXml(0))
        self.add_child(HighConcentrationXml(concentration))
        self.add_child(VendorXml())
        self.add_child(VendorPartNumberXml(local_id))

class StockLocalIdXml(BaseXmlObject):
    def __init__(self, local_id: int):
        super().__init__(name='localID', text=str(local_id))

class StockConcentrationXml(BaseXmlObject):
    def __init__(self, concentration: float):
        super().__init__(name='stockConcentration', text=str(concentration))

class LowConcentrationXml(BaseXmlObject):
    def __init__(self, concentration: float):
        super().__init__(name='defaultLowConcentration', text=str(concentration))

class HighConcentrationXml(BaseXmlObject):
    def __init__(self, concentration: float):
        super().__init__(name='defaultHighConcentration', text=str(concentration))

class UnitsXml(BaseXmlObject):
    def __init__(self, units: str):
        super().__init__(name='units', text=units)

class VendorXml(BaseXmlObject):
    def __init__(self):
        super().__init__(name='vendorName', text='C3')

class VendorPartNumberXml(BaseXmlObject):
    def __init__(self, stock_id: int):
        super().__init__(name='vendorPartNumber', text=f'C3-{stock_id}')


class UseAsBufferXml(BaseXmlObject):
    def __init__(self, buffer: bool):
        super().__init__(name='useAsBuffer', text='true' if buffer else 'false')


class ScreenXml(BaseXmlObject):
    def __init__(self):
        super().__init__(name='screen')
        self.conditions = ConditionsXml()
        self.ingredients = IngredientsXml()

        self.add_child(self.conditions)
        self.add_child(self.ingredients)

    def add_condition(self, condition: ConditionXml):
        self.conditions.add_child(condition)

    def add_ingredient(self, ingredient: IngredientXml):
        self.ingredients.add_child(ingredient)









