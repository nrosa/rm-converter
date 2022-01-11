#import xml.etree.cElementTree as et
from lxml import etree as et
import json
from collections import defaultdict

from constants import chem_groups

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

with open('chem_group_members.json') as fp:
    cgm_data = json.load(fp)
chem_group_members = defaultdict(list)
for cgm in cgm_data:
    group_id = cgm['GROUP_ID']
    if group_id in chem_groups.keys():
        chem_group_members[cgm["CHEMICAL_ID"]].append(chem_groups[group_id])

with open('ph_curves.json') as fp:
    ph_curves_data = json.load(fp)
with open('ph_points.json') as fp:
    ph_points_data = json.load(fp)
ph_curves_id_dict = dict()
for ph_curve in ph_curves_data:
    ph_curves_id_dict[ph_curve["PK_PH_CURVE_ID"]] = ph_curve["FK_CHEMICAL_ID"]
ph_points_dict = defaultdict(list)
for ph_point in ph_points_data:
    ph_points_dict[ph_curves_id_dict[ph_point["FK_PH_CURVE_ID"]]].append(ph_point)


design_root = design_tree.find('reservoir_design')

# Keep track of the ingredient elements with a dict
ingredient_map = dict()
ingredients_xml = et.Element('ingredients')

# Build ingredients and stocks from the recipe file
# Iterate over the stocks in the rigaku recipe
for stock in recipe_root.find('sourceplates').find('sourceplate').find('stocks'):
    # If the ingredient doesn't yet exist create it
    stock_id = int(stock.attrib['barcode'])
    chem_id = stocks_dict[stock_id]['CHEMICAL_ID']


    if chem_id not in ingredient_map.keys():
        # Create a new entry
        ingredient_xml = et.Element('ingredient')
        ingredient_map[chem_id] = ingredient_xml

        name_elem = et.Element('name')
        name_elem.text = chemicals_dict[chem_id]['NAME']
        ingredient_xml.append(name_elem)

        aliases = et.Element('aliases')
        for alias in alias_dict[chem_id]:
            alias_elem = et.Element('alias')
            alias_elem.text = alias
            aliases.append(alias_elem)
        ingredient_xml.append(aliases)

        cas = et.Element('casNumbers')
        cas_number = et.Element('casNumber')
        cas_number.text = chemicals_dict[chem_id]['CAS']
        cas.append(cas_number)
        ingredient_xml.append(cas)

        buffer_flag = False
        types = et.Element('types')
        for chem_type in chem_group_members[chem_id]:
            type_elem = et.Element('type')
            type_elem.text = chem_type
            types.append(type_elem)
            buffer_flag = buffer_flag or chem_type == 'Buffer'
        ingredient_xml.append(types)

        if buffer_flag:
            bd_elem = et.Element('bufferData')
            if chem_id in ph_curves_id_dict.values():
                # TODO Find a C3 recipe that uses ph curves to test this
                raise NotImplementedError()

            else:
                # TODO How does Rockmaker handle ingredients that have multiple pkas?
                if not (chemicals_dict[chem_id]['PKA2'] is None and chemicals_dict[chem_id]['PKA3'] is None):
                    # raise NotImplementedError()
                    pass

                pka_elem = et.Element('pKa')
                pka_elem.text = str(chemicals_dict[chem_id]['PKA1'])
                bd_elem.append(pka_elem)
            ingredient_xml.append(bd_elem)

        # Create all the stock entries
        stocks = et.Element('stocks')
                

    # tree = et.ElementTree(ingredient_xml)
    # tree.write('test.xml', pretty_print=True)
    # exit()
    

    # Add the stock
