import xml.etree.ElementTree as et

from src import objects
from src import utils

def screen_from_rxml(rxml_path: str):
    xml_tree = et.parse(rxml_path)
    xml_root = xml_tree.getroot()

    # Create the ingredients
    ingredients = objects.formtrix.Ingredients()
    for ingredient_xml in xml_root.find('ingredients').findall('ingredient'):
        # Create the buffer data object
        buffer_data_xml = ingredient_xml.find('bufferData')
        buffer_data = None
        if buffer_data_xml is not None:
            # Search for the pka
            pka = buffer_data_xml.find('pKa')
            if pka is not None: pka = float(pka.text)
            # Search for the titration table
            titration_table = None
            tt_xml = buffer_data_xml.find('titrationTable')
            if tt_xml is not None:
                titration_table = objects.formtrix.TitrationTable()
                for point_xml in tt_xml.findall('titrationPoint'):
                    titration_table.add_point(
                        float(point_xml.find('pH').text),
                        int(point_xml.find('acidToBaseRatio').text),
                    )

            buffer_data = objects.formtrix.BufferData(
                pka=pka,
                titration_table=titration_table,
            )

        ingredient = objects.formtrix.Ingredient(
            name = ingredient_xml.find('name').text,
            buffer_data = buffer_data
        )
        # Add aliases
        for alias_xml in ingredient_xml.find('aliases').findall('alias'):
            ingredient.add_alias(alias_xml.text)

        # Add stocks
        for stock_xml in ingredient_xml.find('stocks').findall('stock'):
            ingredient.add_stock(objects.formtrix.Stock(
                local_id = int(stock_xml.find('localID').text),
                conc = float(stock_xml.find('stockConcentration').text),
                units = stock_xml.find('units').text,
                ph = float(stock_xml.find('pH').text) if stock_xml.find('pH') is not None else None,
                buffer = stock_xml.find('useAsBuffer') == 'true',
                part_number = stock_xml.find('vendorPartNumber').text,
                ingredient = ingredient,
            ))

        ingredients.add_ingredient(ingredient)


    # Create the conditions 
    conditions = objects.formtrix.Conditions()
    for i, condition_xml in enumerate(xml_root.find('conditions').findall('condition')):
        condition = objects.formtrix.Condition()
        for cond_ingred_xml in condition_xml.findall('conditionIngredient'):
            # Find the stocks to be used
            local_id = int(cond_ingred_xml.find('stockLocalID').text)
            stock = ingredients.get_stock_by_local_id(local_id)
            high_ph_stock = None
            high_ph_local_id = cond_ingred_xml.find('highPHStockLocalID')
            if high_ph_local_id is not None:
                high_ph_local_id = int(high_ph_local_id.text)
                high_ph_stock = ingredients.get_stock_by_local_id(high_ph_local_id)

            condition.add_condition_ingredient(
                objects.formtrix.ConditionIngredient(
                    conc = float(cond_ingred_xml.find('concentration').text),
                    cond_type = cond_ingred_xml.find('type').text,
                    ph = float(cond_ingred_xml.find('pH').text) if cond_ingred_xml.find('pH') is not None else None,
                    stock = stock,
                    high_ph_stock = high_ph_stock,
                    well_id = i,
            ))

        conditions.add_condition(condition)

    return objects.formtrix.Screen(ingredients, conditions)

def to_xtaltrak_recipe_stock(stock):
    assert isinstance(stock, objects.formtrix.Stock)
    return objects.xtaltrak_recipe_xml.Stock(
        barcode='',
        comments='',
        conc=stock.conc,
        count=stock.get_count(),
        cunits=stock.units,
        density=None,
        name=stock.ingredient.name,
        ph=stock.ph,
        viscosity=None,
        volatility=None,
        volume=stock.get_total_volume(),
        vunits='ul',
    )

def to_xtaltrak_recipe_wellstock(stock):
    assert isinstance(stock, objects.formtrix.Stock)
    well_stock = objects.xtaltrak_recipe_xml.WellStock(
        barcode='',
        comments='',
        conc=stock.conc,
        cunits=stock.units,
        density=None,
        name=stock.ingredient.name,
        ph=stock.ph,
        viscosity=None,
        volatility=None
    )
    for well_id in stock.usages:
        well_stock.add_well(objects.xtaltrak_recipe_xml.Well(
            utils.wellid2name(well_id),
            stock.usages[well_id],
            'ul',
        ))
    return well_stock
        
        
