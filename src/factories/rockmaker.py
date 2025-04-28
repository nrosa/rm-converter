from lxml import etree
from ..objects.rockmaker import Ingredients, TitrationTable, TitrationPoint, BufferData, Ingredient, Stock, Conditions, Condition, ConditionIngredient, Screen
from pathlib import Path

from typing import Optional


def all_children(root, parent, child):
    node = root.find(parent)
    if node is None:
        return []

    return node.findall(child)


def screen_from_rxml_dom(xml_root, name=''):
    # Create the ingredients
    ingredients = Ingredients()
    for ingredient_xml in all_children(xml_root, 'ingredients', 'ingredient'):
        # Create the buffer data object
        buffer_data_xml = ingredient_xml.find('bufferData')
        buffer_data = None
        # bufferData is an optional element
        if buffer_data_xml is not None:
            # Search for the pka
            pka = buffer_data_xml.find('pKa')
            if pka is not None:
                pka = float(pka.text)
            # Search for the titration table
            titration_table = None
            tt_xml = buffer_data_xml.find('titrationTable')
            if tt_xml is not None:
                titration_table = TitrationTable()
                ratio = []
                pH = []
                for point_xml in tt_xml.findall('titrationPoint'):
                    ratio.append(float(point_xml.find('acidToBaseRatio').text))
                    pH.append(float(point_xml.find('pH').text))

                max_ratio = max(ratio)
                scale = 100.0 / max_ratio

                for i in range(len(ratio)):
                    titration_table.append(TitrationPoint(
                        pH[i],
                        scale * ratio[i]))

            buffer_data = BufferData(
                pka=pka,
                titration_table=titration_table,
            )

        ingredient = Ingredient(
            name=ingredient_xml.find('name').text,
            buffer_data=buffer_data
        )
        # Add aliases
        for alias_xml in all_children(ingredient_xml, 'aliases', 'alias'):
            ingredient.add_alias(alias_xml.text)

        # Add stocks
        for stock_xml in all_children(ingredient_xml, 'stocks', 'stock'):
            local_id = int(stock_xml.find('localID').text)
            ingredient.add_stock(Stock(
                local_id=local_id,
                conc=float(stock_xml.find('stockConcentration').text),
                units=stock_xml.find('units').text,
                ph=float(stock_xml.find('pH').text) if stock_xml.find(
                    'pH') is not None else None,
                buffer=stock_xml.find('useAsBuffer') == 'true',
                part_number=stock_xml.find('vendorPartNumber').text if stock_xml.find(
                    'vendorPartNumber') is not None else '',
                vendor=stock_xml.find('vendorName').text if stock_xml.find(
                    # TODO this str needs to be checked against a file from RockMaker
                    'vendorName') is not None else '',
                comments=stock_xml.find('comments').text if stock_xml.find(
                    # TODO this str needs to be checked against a file from RockMaker,
                    'comments') is not None else '',
            ))

        ingredients.append(ingredient)

    # Create the conditions
    conditions = Conditions()
    for i, condition_xml in enumerate(all_children(xml_root, 'conditions', 'condition')):
        condition = Condition()
        for cond_ingred_xml in condition_xml.findall('conditionIngredient'):
            # Find the stocks to be used
            local_id = int(cond_ingred_xml.find('stockLocalID').text)
            # TODO what if a stock is used for multiple ingredients? Could happen with curves?
            ingredient, stock = ingredients.get_ingredient_stock_by_local_id(
                local_id)
            # highPHStockLocalID is an optional element
            high_ph_stock = None
            high_ph_local_id = cond_ingred_xml.find('highPHStockLocalID')
            if high_ph_local_id is not None:
                high_ph_local_id = int(high_ph_local_id.text)
                _, high_ph_stock = ingredients.get_ingredient_stock_by_local_id(
                    high_ph_local_id)

            condition.append(
                ConditionIngredient(
                    conc=float(cond_ingred_xml.find('concentration').text),
                    cond_type=cond_ingred_xml.find('type').text,
                    ingredient=ingredient,
                    ph=float(cond_ingred_xml.find('pH').text) if cond_ingred_xml.find(
                        'pH') is not None else None,
                    stock=stock,
                    high_ph_stock=high_ph_stock,
                    well_id=i,
                ))

        conditions.append(condition)

    return Screen(name, ingredients, conditions)


def screen_from_rxml_file(rxml_path: Path, name=''):
    return screen_from_rxml_dom(etree.parse(rxml_path).getroot(), name=name)


####################################################################################################
# RM db binds
####################################################################################################
# TODO Work in Progress

def stock(stock, context, stock_substitution) -> Optional[Stock]:
    raise NotImplementedError
    if stock is None:
        return None
    stock = context.ingredient_stocks[stock]
    return Stock(
        local_id=None,
        conc=stock.stock_concentration,
        units=stock.units.name,
        ph=stock.pH,
        buffer=stock.use_as_buffer,
        part_number=stock.vendor_part_number,
        vendor=stock.vendor_name,
        comments=stock.comments,
    )


def condition_ingredient(condition_ingredient, context, stock_substitution) -> ConditionIngredient:
    # TODO add phantom highph stock if is buffer and only 1 stock
    # raise Exception(str(type(condition_ingredient)))
    raise NotImplementedError
    return ConditionIngredient(
        conc=condition_ingredient.concentration,
        cond_type=condition_ingredient.chem.active_type,
        ingredient=ingredient(condition_ingredient.chem.id, condition_ingredient.stock_id, context),
        stock=stock(condition_ingredient.stock_id, context, stock_substitution),
        ph=condition_ingredient.pH,
        high_ph_stock=stock(condition_ingredient.high_stock_id, context, stock_substitution)
    )


def ingredient(ingredient_id, stock_id, context) -> Ingredient:
    raise NotImplementedError
    ingredient = context.ingredients[ingredient_id]
    stock = context.ingredient_stocks[stock_id]
    # Stock ingredient is used to find the buffer data as it may differ from the ingredient
    # in a titration curve
    stock_ingredient = stock.ingredient

    # Find the buffer data
    # TODO check if ingredient is a buffer
    titration_table = None
    buffer_data = None
    if ingredient.pKa is None:
        titration_curve = context.ingredient_titration_curves.get(stock_ingredient, None)
        if not titration_curve is None:
            titration_table = TitrationTable([TitrationPoint(ph=x.pH, a2b_ratio=x.ratio) for x in titration_curve])
    if titration_table is not None or ingredient.pKa is not None:
        buffer_data = BufferData(
            pka=ingredient.pKa,
            titration_table=titration_table,
        )

    cas_number = context.ingredient_cas_numbers.get(ingredient, [None])[0]

    return Ingredient(
        name=str(ingredient.name),
        cas_number=cas_number,
        shortname=str(ingredient.short_name),
        buffer_data=buffer_data,
    )
