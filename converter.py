import xml.etree.ElementTree as et
import json
from collections import defaultdict

# Construct the conditions
design_tree = et.parse('Shotgun.xml')
recipe_tree = et.parse('Shotgun_recipe.xml')
recipe_root = recipe_tree.getroot()

# Open and process the json files
with open('chemicals.json') as fp:
    chemicals_data = json.load(fp)
chemicals_dict = dict()
for chem in chemicals_data['CHEMICALS']:
    chemicals_dict[chem['CHEMICAL_ID']]=chem

with open('stocks.json') as fp:
    stocks_data = json.load(fp)
stocks_dict = dict()
for stock in stocks_data['STOCKS']:
    stocks_dict[stock['STOCK_ID']]=stock

with open('chemical_alias.json') as fp:
    alias_data = json.load(fp)
alias_dict = defaultdict(list)
for alias in alias_data['CHEMICAL_ALIAS']:
    alias_dict[alias['CHEMICAL_ID']].append(alias['CHEM_ALIAS'])


design_root = design_tree.find('reservoir_design')

# Keep track of the ingredient elements with a dict
ingredient_map = dict()
ingredients_xml = et.Element('ingredients')

# Build ingredients and stocks from the recipe file
# Iterate over the stocks
for stock in recipe_root.find('sourceplates').find('sourceplate').find('stocks'):
    # If the ingredient doesn't yet exist create it
    stock_id = int(stock.attrib['barcode'])
    chem_id = stocks_dict[stock_id]['CHEMICAL_ID']

    print(chemicals_dict[chem_id])

    if chem_id not in ingredient_map.keys():
        # Create a new entry
        ingredient_xml = et.Element('ingredient')
        ingredient_map[chem_id] = ingredient_xml

        ingredient_xml.append(et.Element('stocks'))
        ingredient_xml.append(et.Element(
            'name',
            text=chemicals_dict[chem_id]['NAME']
        ))

        aliases = et.Element('aliases')
        for alias in alias_dict[chem_id]:
            aliases.append(et.Element('alias', text=alias))
        ingredient_xml.append(aliases)

        cas = et.Element('casNumbers')
        cas.append(et.Element(
            'casNumber',
            text=chemicals_dict[chem_id]['CAS']
        ))
        ingredient_xml.append(cas)

        ingredient_xml.append(et.Element(
            'name',
            text=chemicals_dict[chem_id]['NAME']
        ))

        types = et.Element('types')
        






    print(chem_id)
    exit()
    

    # Add the stock
