import xml.etree.ElementTree as et

from src import objects

def screen_from_rxml(rxml_path: str):
    xml_tree = et.parse(rxml_path)
    xml_root = xml_tree.getroot()

    # Create the conditions 
    conditions = objects.formtrix.Conditions()
    for condition_xml in xml_root.find('conditions').findall('condition'):
        condition = objects.formtrix.Condition()
        for cond_ingred_xml in condition_xml.findall('conditionIngredient'):
            condition.add_condition_ingredient(
                objects.formtrix.ConditionIngredient(
                    conc = float(cond_ingred_xml.find('concentration').text),
                    cond_type = cond_ingred_xml.find('type').text,
                    local_id = int(cond_ingred_xml.find('stockLocalID').text),
            ))

        conditions.add_condition(condition)


    # Create the ingredients
    ingredients = objects.formtrix.Ingredients()
    for ingredient_xml in xml_root.find('ingredients').findall('ingredient'):
        ingredient = objects.formtrix.Ingredient(
            name = ingredient_xml.find('name').text,
        )
        # Add aliases
        for alias_xml in ingredient_xml.find('aliases').findall('alias'):
            ingredient.add_alias(alias_xml.text)

        # Add stocks
        for stock_xml in ingredient_xml.find('stocks').findall('stock'):
            ingredient.add_stock(objects.formtrix.Stock(
                local_id = int(stock_xml.find('localID').text),
                units = stock_xml.find('units').text,
                buffer = stock_xml.find('useAsBuffer') == 'true',
            ))

        ingredients.add_ingredient(ingredient)

    return objects.formtrix.Screen(ingredients, conditions)
        
