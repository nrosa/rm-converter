from __future__ import annotations
from typing import Optional, Set, Iterable
import numpy as np
import warnings
from lxml import etree

from .. import utils
from .base import BaseXml, ListXml, SetXml, IndexedListXml, PhMixin
from ..config import constants

####################################################################################################
# Mixins
####################################################################################################


class RecipeVolumeMixin:
    def add_recipe_volume(self, volume, *, require_exact_ph):
        for child in self:
            child.add_recipe_volume(
                volume, require_exact_ph=require_exact_ph)


####################################################################################################
# Simple XML Container classes
####################################################################################################

class Condition(ListXml, RecipeVolumeMixin):
    def __init__(self):
        super().__init__(name='condition')


class Conditions(ListXml, RecipeVolumeMixin):
    def __init__(self):
        super().__init__(name='conditions')


class Ingredients(IndexedListXml):
    def __init__(self):
        super().__init__(name='ingredients', key=lambda x: x.ingredient_name)

    def get_ingredient_stock_by_local_id(self, local_id: int):
        for ingredient in self:
            for stock in ingredient.stocks:
                if stock.localID == local_id:
                    return ingredient, stock
        return None, None


class TitrationTable(ListXml):
    def __init__(self, *args, **kwargs):
        super().__init__(name='titrationTable', *args, **kwargs)

####################################################################################################
# TODO Name this section
####################################################################################################


class TitrationPoint(BaseXml, PhMixin):
    # __slots__ = ['ph', 'a2b_ratio']

    def __init__(self, ph: float, a2b_ratio: float):
        super().__init__(name='titrationPoint',
                         children=['pH', 'acidToBaseRatio'])
        self.ph = ph
        self.acidToBaseRatio = a2b_ratio


class BufferData(BaseXml):
    # __slots__ = ['pka', 'titration_table']

    def __init__(self, pka: float = None, titration_table: TitrationTable = None):
        super().__init__(name='bufferData',
                         children=['pKa', 'titration_table'])
        assert pka is not None or titration_table is not None
        self.pka = pka
        self.titration_table = titration_table

    @property
    def pKa(self):
        return self.pka


class ConditionIngredient(BaseXml, PhMixin):
    # __slots__ = [
    # 'conc','type','ph','stock','high_ph_stock','well_id','volume','high_ph_volume',
    # ]

    def __init__(self,
                 conc: float,
                 cond_type: str,
                 ingredient: Ingredient,
                 stock: Stock,
                 ph: Optional[float] = None,
                 high_ph_stock: Optional[Stock] = None,
                 well_id: Optional[int] = None,
                 ):
        super().__init__(name='conditionIngredient', children=[
            'concentration', 'pH', 'type', 'stockLocalID', 'highPHStockLocalID'])

        self.concentration = conc
        self.type = cond_type
        self.ph = ph
        self.ingredient = ingredient
        self.stock = stock
        self.high_ph_stock = high_ph_stock
        self.well_id = well_id

        # Add the type of this condition ingredient to the ingredients
        self.ingredient.add_type(self.type)

    @property
    def stockLocalID(self):
        if self.stock is not None:
            if self.stock.localID is not None:
                return self.stock.localID
            raise Exception(
                f'None localID for ConditionIngredient {self.ingredient.ingredient_name}')
        raise Exception('Stock is None')

    @property
    def highPHStockLocalID(self):
        if self.high_ph_stock is not None:
            if self.high_ph_stock.localID is not None:
                return self.high_ph_stock.localID
            raise Exception(
                f'None localID for ConditionIngredient {self.ingredient.ingredient_name}')
        return None

    def check_exact_ph(self, raise_error: bool = False):
        if self.ph != self.stock.ph:
            mesg = f"desired pH ({self.ph}) does not match stock pH ({self.stock.ph}) in well \
                {utils.wellid2name(self.well_id + 1)}"
            if raise_error:
                raise Exception(mesg)
            else:
                warnings.warn(mesg)

    def add_recipe_volume(self, well_volume, *, require_exact_ph):
        total_volume = (well_volume * self.concentration) / \
            self.stock.stockConcentration
        self.volume = None
        self.high_ph_volume = None

        if self.type == 'Buffer':
            if self.high_ph_stock is not None:
                no_buffer_data = Exception(
                    f'No pka or titration table for buffer: {self.ingredient.ingredient_name}')

                if self.ingredient.buffer_data is None:
                    raise no_buffer_data

                # Calc the volume with the henderson hasselback
                if self.ingredient.buffer_data.pka is not None:
                    pka = self.ingredient.buffer_data.pka
                    low_fraction = utils.henderson_hasselbach_mix(pka=pka,
                                                                  low_ph=self.stock.ph,
                                                                  high_ph=self.high_ph_stock.ph,
                                                                  desired_ph=self.ph)
                    assert self.stock.stockConcentration == self.high_ph_stock.stockConcentration

                    self.volume = low_fraction * total_volume
                    self.high_ph_volume = (1-low_fraction) * total_volume

                elif self.ingredient.buffer_data.titration_table is not None:
                    a2b_ratio = None
                    min_dist = np.inf
                    for point in self.ingredient.buffer_data.titration_table:
                        dist = np.abs(point.ph - self.ph)
                        if dist < min_dist:
                            min_dist = dist
                            a2b_ratio = point.acidToBaseRatio
                    low_fraction = a2b_ratio / 100

                    self.volume = low_fraction * total_volume
                    self.high_ph_volume = (1-low_fraction) * total_volume
                else:
                    raise no_buffer_data
            else:
                self.check_exact_ph(require_exact_ph)
                self.volume = total_volume
        else:
            # Easy case
            self.volume = total_volume

        # Track the total volumes
        if self.volume is not None:
            self.volume = round(self.volume, constants.CONC_PREC)
            self.stock.add_usage(self.well_id, self.volume)
        if self.high_ph_volume is not None:
            self.high_ph_volume = round(
                self.high_ph_volume, constants.CONC_PREC)
            self.high_ph_stock.add_usage(self.well_id, self.high_ph_volume)

        if self.high_ph_stock is not None:
            if self.high_ph_volume is None:
                raise Exception(
                    f'High pH volume is None for {self.ingredient.ingredient_name} in well {utils.wellid2name(self.well_id + 1)}, {self.stock.ph}, {self.high_ph_stock.ph}')


class Stock(BaseXml, PhMixin):
    # __slots__ = ['local_id','conc','units','ph','buffer','part_number', 'usages']
    def __init__(self,
                 local_id: Optional[int],
                 conc: float,
                 units: str,
                 ph: Optional[float],
                 buffer: bool,
                 part_number: Optional[str],
                 vendor: Optional[str],
                 comments: Optional[str],
                 ):
        super().__init__(name='stock', children=[
            'localID', 'stockConcentration', 'defaultLowConcentration', 'defaultHighConcentration', 'units', 'pH', 'useAsBuffer', 'vendorPartNumber', 'vendorName', 'comments'])
        self.localID = local_id
        self.stockConcentration = conc
        self.defaultLowConcentration = 0
        self.defaultHighConcentration = conc
        self.units = units
        self.ph = ph
        self.buffer = buffer
        self.vendorPartNumber = part_number
        self.vendorName = vendor
        self.comments = comments

        # Used to track total volume in screen
        # {well_number: volume}
        self.usages = dict()

    @property
    def useAsBuffer(self):
        return 'true' if self.buffer else 'false'

    def add_local_id(self, local_id: int):
        self.localID = local_id

    def add_usage(self, well_id, volume):
        self.usages[well_id] = volume

    def get_count(self):
        return len(self.usages)

    def get_total_volume(self):
        return sum([self.usages[x] for x in self.usages])


class Ingredient(BaseXml):
    def __init__(self,
                 name: str,
                 cas_number: Optional[str] = None,
                 shortname: Optional[str] = None,
                 buffer_data: Optional[BufferData] = None,
                 name_substitution: Optional[bool] = True,
                 types: Iterable[str] = [],
                 aliases: Iterable[str] = [],
                 ):
        super().__init__(name='ingredient', children=[
            'stocks_xml', 'types_xml', 'buffer_data_xml', 'cas_numbers', 'name', 'shortName'])
        self.ingredient_name = name
        self.buffer_data = buffer_data
        self.cas_number = cas_number
        self.shortname = shortname
        self.name_substitution = name_substitution
        self.aliases = set(aliases)
        self.stocks = set()
        self.types = set(types)

    @property
    def stocks_xml(self):
        stocks = sorted(self.stocks, key=lambda x: x.localID)
        return ListXml(stocks, name='stocks')

    @property
    def buffer_data_xml(self):
        return self.buffer_data if constants.BUFFER in self.types else None

    # TODO Can make cas numbers track multiple
    @property
    def cas_numbers(self):
        if self.cas_number is not None:
            cas_numbers = SetXml(name='casNumbers')
            cas_numbers.add(
                BaseXml(text=str(self.cas_number), name='casNumber'))
            return cas_numbers
        return None

    @property
    def shortName(self):
        return utils.prefix_str(constants.LAB_NAME, self.shortname, self.name_substitution)

    @property
    def name(self):
        return utils.suffix_str(self.ingredient_name, f' {constants.LAB_NAME}', self.name_substitution)

    @property
    def aliases_xml(self):
        sorted_aliases = sorted([str(x) for x in self.aliases])
        return SetXml([BaseXml(name='alias', text=x) for x in sorted_aliases], name='aliases')

    @property
    def types_xml(self):
        sorted_types = sorted([str(x) for x in self.types])
        return SetXml([BaseXml(name='type', text=str(x)) for x in sorted_types], name='types')

    def add_stock(self, stock: Stock):
        self.stocks.add(stock)

    def add_alias(self, alias: str):
        self.aliases.add(alias)

    def add_type(self, type: str):
        self.types.add(type)


class Screen(BaseXml):
    # __slots__ = ['name', 'ingredients','conditions', 'volume']

    def __init__(
            self,
            name: str,
            ingredients: Optional[Ingredients] = None,
            conditions: Optional[Conditions] = None
    ):
        super().__init__(name='screen', children=['conditions', 'ingredients'])
        self.ingredients = Ingredients() if ingredients is None else ingredients
        self.conditions = Conditions() if conditions is None else conditions
        self.name = name
        self.volume = None

    def add_recipe_volume(self, volume, *, require_exact_ph):
        self.volume = volume
        self.conditions.add_recipe_volume(
            volume, require_exact_ph=require_exact_ph)

    def get_stocks(self) -> Set[Stock]:
        global_stocks = set()
        for ingredient in self.ingredients:
            for stock in ingredient.stocks:
                global_stocks.add(stock)
        return global_stocks

    def get_ingredient_by_name(self, name: str) -> Optional[Ingredient]:
        if name in self.ingredients._index:
            return self.ingredients[self.ingredients.index_of(name)]
        return None

    def get_max_local_id(self) -> int:
        max_stock = max(self.get_stocks(),
                        key=lambda x: x.localID, default=None)
        return 0 if max_stock is None else max_stock.localID

    def get_stock(self,
                  ingredient_name: str,
                  conc: float,
                  units: str,
                  ph: Optional[float] = None
                  ) -> Optional[Stock]:
        ingredient = self.get_ingredient_by_name(ingredient_name)
        if ingredient is not None:
            for stock in ingredient.stocks:
                if stock.stockConcentration == conc and stock.units == units and stock.ph == ph:
                    return stock
        return None

    def add_condition(self, condition: Condition):
        # Make sure that the stocks and ingredients are unified.
        for ci in condition:
            ci = self.merge_condition_ingredient_stocks(ci)
        self.conditions.append(condition)

    def merge_condition_ingredient_stocks(self, ci: ConditionIngredient) -> ConditionIngredient:
        '''
        Merges the given condition ingredient's stock solutions with the existing stocks in this 
        screen to ensure there is no duplication.
        '''
        ci.ingredient = self.add_ingredient(
            ci.ingredient.name,
            ci.ingredient.cas_number,
            ci.ingredient.shortname,
            ci.ingredient.buffer_data,
            ci.ingredient.name_substitution,
            ci.ingredient.types,
            ci.ingredient.aliases,
        )
        ci.stock = self.add_stock_object(
            ingredient_name=ci.ingredient.name, stock=ci.stock)
        ci.high_ph_stock = self.add_stock_object(
            ingredient_name=ci.ingredient.name, stock=ci.high_ph_stock)
        return ci

    def add_stock_object(
        self,
        ingredient_name: str,
        stock: Optional[Stock]
    ) -> Stock:
        '''
        Takes a stock (containing an ingredient) and adds copies of them both to the screen.

        Returns: 
            Stock: The added stock. 
        If either the stock or ingredient already exist then the return
        value is updated to include the preexisting objects.
        '''
        if stock is None:
            return None
        # Check for existing stocks
        existing_stock = self.get_stock(
            ingredient_name, stock.stockConcentration, stock.units, stock.ph)
        if existing_stock is not None:
            return existing_stock

        # Add this stock to the existing ingredient
        return self.add_stock(
            ingredient_name,
            stock.stockConcentration,
            stock.units,
            stock.ph,
            stock.buffer,
            stock.vendorPartNumber,
            stock.vendorName,
            stock.comments
        )

    def add_stock(
        self,
        ingredient_name: str,
        conc: float,
        units: str,
        ph: Optional[float],
        buffer: bool,
        part_number: str,
        vendor: str,
        comments: str
    ) -> Stock:
        if self.get_stock(ingredient_name, conc, units, ph) is not None:
            raise Exception("Tried to add a stock that already exists.")
        ingredient = self.get_ingredient_by_name(ingredient_name)
        if ingredient is None:
            raise Exception(
                'The provided info does not match any existing ingredient.')
        stock = Stock(
            local_id=self.get_max_local_id() + 1,
            conc=conc,
            units=units,
            ph=ph,
            buffer=buffer,
            part_number=part_number,
            vendor=vendor,
            comments=comments,
        )
        ingredient.add_stock(stock)
        return stock

    def add_ingredient(
        self,
        name: str,
        cas_number: Optional[str] = None,
        shortname: Optional[str] = None,
        buffer_data: Optional[BufferData] = None,
        name_substitution: Optional[bool] = True,
        types: Iterable[str] = [],
        aliases: Iterable[str] = [],
    ) -> Ingredient:
        '''
        Adds a new ingredient to the screen and returns it.
        If the ingredient already exists then the existing ingredient is return
        '''
        # Check ingredient name
        ei = self.get_ingredient_by_name(name)
        if ei is not None:
            # Add buffer data if it does not already exist
            if ei.buffer_data is None and buffer_data is not None:
                ei.buffer_data = buffer_data
            ei.aliases = ei.aliases | set(aliases)
            ei.types = ei.types | set(types)
            return ei  # TODO check whether these ingredients are actually the same
        ingredient = Ingredient(
            name, cas_number, shortname, buffer_data, name_substitution, types=types, aliases=aliases)
        self.ingredients.append(ingredient)
        return ingredient

    def get_xml_element(self) -> etree.Element:
        element = super().get_xml_element()
        element.addprevious(etree.Comment(constants.RM_COMMENT))
        return element
