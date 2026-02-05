from __future__ import annotations

from ..objects import rockmaker as objects_rm
from ..objects import xtaltrak as objects_xt
from ..factories import xtaltrak as factories_xt

from .. import utils
from ..config import constants
from ..recipe import pick_stocks_for_well

from typing import List, Optional

####################################################################################################
# Rockmaker to Xtaltrak
####################################################################################################


def rm2xt_stock(
        rm_stock: objects_rm.Stock,
        rm_ingred: objects_rm.Ingredient,
        stocks_f: Optional[factories_xt.StocksFactory] = None,
    ) -> objects_xt.Stock:
    # Fill in the missing (None) values with stock data if available
    barcode = None

    # If we can find a matching stock in the stocks factory, use its properties
    if rm_stock.vendorPartNumber is not None:
        barcode = utils.partnumber_to_barcode(rm_stock.vendorPartNumber)
        if stocks_f is not None and barcode:
            stock_id = None
            try:
                stock_id = int(barcode)
            except ValueError:
                pass
            if stock_id is not None:
                stock = stocks_f.get_stock_by_id(stock_id)
                if stock is not None:
                    return stock

    xt_stock = objects_xt.Stock(
        stock_id=None,
        stock_name=rm_ingred.ingredient_name,
        chem=rm2xt_chem(rm_ingred),
        conc=rm_stock.stockConcentration,
        units=rm_stock.units,
        ph=rm_stock.ph,
        viscosity=None,
        volatility=None,
        lid_name=None,
        barcode=barcode,
        density=None,
        comments=constants.DEFAULT_COMMENT,
    )
    for well_id in rm_stock.usages:
        xt_stock.add_well(objects_xt.Well(
            utils.wellid2name(well_id + 1),
            rm_stock.usages[well_id],
        ))
    return xt_stock


def rm2xt_chem(ingredient: objects_rm.Ingredient) -> objects_xt.Chemical:
    pkas = []
    if ingredient.buffer_data is not None:
        if ingredient.buffer_data.pka is not None:
            pkas.append(ingredient.buffer_data.pka)
    return objects_xt.Chemical(
        chem_id=None,
        name=ingredient.ingredient_name,
        cas=ingredient.cas_number,
        pkas=pkas,
        aliases=[x for x in ingredient.aliases],
    )


def rmscreen2xtrecipe(
        rm_screen: objects_rm.Screen,
        stocks_f: Optional[factories_xt.StocksFactory] = None,
    ) -> objects_xt.SourcePlate:
    # TODO check volume has been created
    sp = objects_xt.SourcePlate(
        description=constants.DEFAULT_DESC,
        name=rm_screen.name,
        volume=rm_screen.volume
    )
    # stock_name -> xt_stock
    stock_map = {}

    def add_stock(rm_stock, rm_ingredient, volume, well_id):
        if volume is None:
            raise ValueError(f"Volume is None for stock {rm_stock.localID} in well {utils.wellid2name(well_id)}")
        xt_stock = rm2xt_stock(
            rm_stock=rm_stock,
            rm_ingred=rm_ingredient,
            stocks_f=stocks_f
        )
        if xt_stock.stock_name not in stock_map:
            stock_map[xt_stock.stock_name] = xt_stock
        xt_stock = stock_map[xt_stock.stock_name]
        # Add the volume
        xt_stock.add_well(objects_xt.Well(
            utils.wellid2name(well_id),
            volume
        ))
        
    for i, cond in enumerate(rm_screen.conditions):
        for cond_ingred in cond:
            add_stock(cond_ingred.stock, cond_ingred.ingredient,
                      cond_ingred.volume, i + 1)
            
            if cond_ingred.high_ph_stock is not None:
            # If there is a high pH stock, add it as well
                add_stock(cond_ingred.high_ph_stock, cond_ingred.ingredient,
                            cond_ingred.high_ph_volume, i + 1)

    # Add all the stocks in the stock_map to the source plate
    for stock in stock_map.values():
        sp.stocks.append(stock)
    

    return sp


####################################################################################################
# Xtaltrak to Rockmaker
####################################################################################################

def xt2rm_stock(
    xt_stock: objects_xt.Stock,
    is_buffer: bool = False,
) -> objects_rm.Stock:
    rm_stock = objects_rm.Stock(
        local_id=None,
        conc=xt_stock.conc,
        units=xt_stock.units,
        ph=xt_stock.ph,
        buffer=is_buffer,
        part_number=f'{constants.PARTNUMBER_PREFIX}-{xt_stock.barcode}',
        vendor=constants.PARTNUMBER_PREFIX,
        comments=xt_stock.comments,
    )
    return rm_stock


def designitem2conditioningredient(
        di: objects_xt.DesignItem,
        stock: objects_xt.Stock,
        high_stock: Optional[objects_xt.Stock],
        well_id: Optional[int],
        phcurve_f: Optional[factories_xt.PhCurveFactory] = None,
        stocks_f: Optional[factories_xt.StocksFactory] = None,
        include_aliases: Optional[bool] = False,
) -> objects_rm.ConditionIngredient:
    rm_stock = xt2rm_stock(stock, is_buffer=di.is_buffer)
    ingredient = chemical2ingredient(
        chem=di.chemical, ph=stock.ph, phcurve_f=phcurve_f, stocks_f=stocks_f, include_aliases=include_aliases)
    ingredient.stocks.add(rm_stock)
    rm_high_stock = None
    if high_stock is not None:
        rm_high_stock = xt2rm_stock(
            high_stock, is_buffer=di.is_buffer,)
        ingredient.stocks.add(rm_high_stock)
    return objects_rm.ConditionIngredient(
        conc=di.concentration,
        cond_type=di.item_class,
        ingredient=ingredient,
        stock=rm_stock,
        ph=di.ph,
        high_ph_stock=rm_high_stock,
        well_id=well_id,
    )


def chemical2ingredient(
        chem: objects_xt.Chemical,
        phcurve_f: Optional[factories_xt.PhCurveFactory],
        stocks_f: Optional[factories_xt.StocksFactory],
        ph: Optional[bool] = None,
        include_aliases: Optional[bool] = False,
) -> objects_rm.Ingredient:
    # Create the buffer data
    buffer_data = None
    if phcurve_f is not None and phcurve_f.is_chem_curve(chem.id):
        curve = phcurve_f.get_curve_by_chem_id(chem.id)
        points = objects_rm.TitrationTable()
        for point in curve.points:
            points.append(objects_rm.TitrationPoint(
                point.ph, point.acid_fraction))
        buffer_data = objects_rm.BufferData(
            titration_table=points)
    else:
        if len(chem.pkas) > 0:
            chosen_pka = chem.pkas[0]
            # TODO just take the first pka for now to match the old code
            # if ph is not None:
            #     min_dist = abs(chosen_pka-ph)
            #     for pka in chem.pkas[1:]:
            #         dist = abs(pka-ph)
            #         if dist < min_dist:
            #             min_dist = dist
            #             chosen_pka = pka
            buffer_data = objects_rm.BufferData(pka=chosen_pka)
        else:
            pass  # TODO Exception?

    ingred = objects_rm.Ingredient(
        name=chem.name,
        cas_number=chem.cas if chem.cas else '-1',
        shortname=chem.shortname,
        buffer_data=buffer_data,
    )
    if include_aliases:
        for alias in chem.aliases:
            ingred.aliases.add(alias)
    return ingred


def designwell2condition(
        designwell: objects_xt.DesignWell,
        stocks: List[objects_xt.Stock],
        well_id: Optional[int] = None,
        phcurve_f: Optional[factories_xt.PhCurveFactory] = None,
        stocks_f: Optional[factories_xt.StocksFactory] = None,
        include_aliases: Optional[bool] = False,
) -> objects_rm.Condition:
    condition = objects_rm.Condition()
    for di, (stock, high_stock) in zip(designwell.items, stocks):
        # Only add design items that have a concentration above zero
        if di.concentration > 0:
            condition.append(designitem2conditioningredient(
                di=di,
                stock=stock,
                high_stock=high_stock,
                well_id=well_id,
                phcurve_f=phcurve_f,
                stocks_f=stocks_f,
                include_aliases=include_aliases
            ))
    return condition


def design2screen(
        design: objects_xt.Design,
        recipe: Optional[objects_xt.SourcePlate],
        stocks_f: factories_xt.StocksFactory,
        phcurve_f: factories_xt.PhCurveFactory,
        require_exact_ph: bool,
        include_aliases: Optional[bool] = False,
) -> objects_rm.Screen:
    # Required for buffer class fixes
    design.set_one_ph()
    screen = objects_rm.Screen(name=design.name)

    for well_id, dw in design.wells.items():
        # Get the stocks
        if recipe is None:
            stocks = pick_stocks_for_well(
                dw,
                stocks_f=stocks_f,
                phcurve_f=phcurve_f,
                require_exact_ph=require_exact_ph
            )
            # Set the one_stock property
            for di, (_, high_stock) in zip(dw.items, stocks):
                di.one_stock = high_stock == None
        else:
            well_stocks = recipe.get_stocks_for_well(well_id)
            # Sort the stocks into (low_stock, high_stock) for each design item
            sorted_stocks = []
            for di in dw.items:
                low_stock, high_stock = None, None
                # Find the stocks for this di
                di_stocks = [
                    x for x in well_stocks if x.chem.id == di.chemical.id]
                di.one_stock = len(di_stocks) == 1

                di_chem_ids = None
                if di.is_buffer:
                    curve = phcurve_f.get_curve_by_chem_id(di.chemical.id)
                    if curve is None:
                        di_chem_ids = (di.chemical.id,)
                    else:
                        if curve.low_chem.id == curve.high_chem.id:
                            di_chem_ids = (curve.low_chem.id,)
                        else:
                            di_chem_ids = (curve.low_chem.id,
                                           curve.high_chem.id)

                else:
                    di_chem_ids = (di.chemical.id,)

                chem_stocks = [
                    x for x in well_stocks if x.chem.id in di_chem_ids]

                low_stock = chem_stocks[0]
                if len(chem_stocks) == 2:
                    high_stock = chem_stocks[1]
                if high_stock is not None and high_stock.ph is None:
                    raise Exception(f"High stock {high_stock.name} in well {utils.wellid2name(well_id)} {well_id} has no pH value.")
                if high_stock is not None and low_stock.ph > high_stock.ph:
                    low_stock, high_stock = high_stock, low_stock

                sorted_stocks.append((low_stock, high_stock))
            stocks = sorted_stocks

        screen.add_condition(designwell2condition(
            designwell=dw, stocks=stocks, well_id=well_id, phcurve_f=phcurve_f, stocks_f=stocks_f, include_aliases=include_aliases))

    return screen
