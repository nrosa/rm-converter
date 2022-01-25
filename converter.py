#import xml.etree.cElementTree as et
from lxml import etree as et
import json
from collections import defaultdict
import warnings

from constants import chem_groups

LOCAL_ID_CNTR = 0
def get_new_localid():
    global LOCAL_ID_CNTR
    LOCAL_ID_CNTR += 1
    return LOCAL_ID_CNTR

def wellname2id(name):
    well_id = (ord(name[0]) - ord('A'))*12 + int(name[1:])
    return well_id

def frac2ratio(base_frac):
    acid_frac = 100 - base_frac
    return acid_frac / base_frac


# Construct the conditions
design_tree = et.parse('Shotgun.xml')
design_root = design_tree.getroot()
recipe_tree = et.parse('Shotgun_recipe.xml')
recipe_root = recipe_tree.getroot()


# Open and process the json files
with open('chemicals.json') as fp:
    chemicals_data = json.load(fp)
chemicals_dict = dict()
chemicals_name2id = dict()
for chem in chemicals_data['CHEMICALS']:
    chemicals_dict[chem['CHEMICAL_ID']] = chem
    chemicals_name2id[chem['NAME'].lower()] = chem['CHEMICAL_ID']

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
# Chem id is the key of ph_curves_dict
ph_curves_dict = dict()
for ph_curve in ph_curves_data:
    ph_curves_id_dict[ph_curve["PK_PH_CURVE_ID"]] = ph_curve["FK_CHEMICAL_ID"]
    ph_curves_dict[ph_curve['FK_CHEMICAL_ID']] = ph_curve
# Chem id is the key
ph_points_dict = defaultdict(list)
for ph_point in ph_points_data:
    # chem_id is the key for ph_points_dict
    ph_points_dict[ph_curves_id_dict[ph_point["FK_PH_CURVE_ID"]]].append(ph_point)


design_root = design_tree.find('reservoir_design')


screen = et.Element('screen')
conditions_xml = et.Element('conditions')
screen.append(conditions_xml)
ingredients_xml = et.Element('ingredients')
screen.append(ingredients_xml)

# Track the ingredients which have been created
ingredient_stock_map = dict()
stock_to_lid_map = dict()
lid_ph_dict = dict()

# Iterate over each condition find the ingredients and the stocks
for well in design_root.findall('well'):
    well_id = int(well.attrib['number'])
    condition_xml = et.Element('condition')
    conditions_xml.append(condition_xml)

    for item in well:
        # Find the name based upon the chemical name
        chem_id  = chemicals_name2id[item.attrib['name'].lower()]
        if chem_id not in ingredient_stock_map:
            # If the ingredient isnt in the ingredient stock map then we have not created it yet
            ingredient_xml = et.Element('ingredient')

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
                bd_xml = et.Element('bufferData')
                if chem_id in ph_curves_id_dict.values():
                    tt_xml = et.Element('titrationTable')
                    bd_xml.append(tt_xml)
                    for ph_point in ph_points_dict[chem_id]:
                        # Skip the first point because formulatrix uses a ratio which is infinit
                        # for entirely base
                        if ph_point['HIGH_PH_FRACTION_X'] == 0:
                            continue
                        point_xml = et.Element('titrationPoint')
                        tt_xml.append(point_xml)
                        point_ph_xml = et.Element('pH')
                        point_xml.append(point_ph_xml)
                        point_ratio_xml = et.Element('acidToBaseRatio')
                        point_xml.append(point_ratio_xml)

                        point_ph_xml.text = str(ph_point['RESULT_PH_Y'])
                        point_ratio_xml.text = str(frac2ratio(ph_point['HIGH_PH_FRACTION_X']))
                else:
                    # TODO How does Rockmaker handle ingredients that have multiple pkas?
                    if not (chemicals_dict[chem_id]['PKA2'] is None and chemicals_dict[chem_id]['PKA3'] is None):
                        # raise NotImplementedError()
                        chem_name = chemicals_dict[chem_id]["NAME"]
                        warnings.warn(f'Warning: Chemical {chem_id}:{chem_name} has multiple pkas')
                        

                    pka_xml = et.Element('pKa')
                    pka_xml.text = str(chemicals_dict[chem_id]['PKA1'])
                    bd_xml.append(pka_xml)
                ingredient_xml.append(bd_xml)

            stocks_xml = et.Element('stocks')
            ingredient_xml.append(stocks_xml)
            ingredients_xml.append(ingredient_xml)

            # Add ingredient xml to the dict
            ingredient_stock_map[chem_id] = stocks_xml


        # Find the stocks for this ingredient in this well for this item
        # The list of stocks that are in this well and a part of the current item
        stock_lids_lst = []
        # The list of chemical ids that are used in stocks for the current ingredient
        # Is usually only one but can be two if the ingredient is a fundamental mixture
        chem_id_lst = []
        if chem_id in ph_curves_id_dict.values():
            chem_id_lst.append(ph_curves_dict[chem_id]['LOW_SOURCE_ID'])
            chem_id_lst.append(ph_curves_dict[chem_id]['HIGH_SOURCE_ID'])
        else:
            chem_id_lst.append(chem_id)

        for stock in recipe_root.find('sourceplates').find('sourceplate').find('plate').find('wells'):
            stock_chem_id = stocks_dict[int(stock.attrib['barcode'])]['CHEMICAL_ID']
            if stock_chem_id in chem_id_lst:
                # This stock is possibly used by the ingredient
                used_flag = False
                for well in stock:
                    # This stock is used in this ingredient so add it
                    if wellname2id(well.attrib['name']) == well_id:
                        used_flag = True
                # Havent come accross this stock yet so create it
                if used_flag:
                    if stock.attrib['barcode'] not in stock_to_lid_map.keys():
                    
                        stocks_xml = ingredient_stock_map[chem_id]
                        stock_xml = et.Element('stock')
                        stock_lid = get_new_localid()

                        stock_concentration = et.Element('stockConcentration')
                        stock_concentration.text = stock.attrib['conc']
                        stock_xml.append(stock_concentration)

                        stock_units = et.Element('units')
                        stock_units.text = stock.attrib['cunits']
                        stock_xml.append(stock_units)

                        is_buffer = et.Element('useAsBuffer')
                        if stock.attrib['pH'] == "":
                            is_buffer.text = 'false'
                            stock_xml.append(is_buffer)
                            lid_ph_dict[stock_lid] = None
                        else:
                            is_buffer.text = 'true'
                            stock_xml.append(is_buffer)

                            ph = et.Element('pH')
                            ph.text = stock.attrib['pH']
                            stock_xml.append(ph)
                            lid_ph_dict[stock_lid] = float(stock.attrib['pH'])

                        stocks_xml.append(stock_xml)

                        stock_to_lid_map[stock.attrib['barcode']] = stock_lid

                    stock_lids_lst.append(stock_to_lid_map[stock.attrib['barcode']])

       

        # Add the conditions to the well
        item_xml = et.Element('conditionIngredient')
        condition_xml.append(item_xml)

        item_type_xml = et.Element('type')
        buffer_flag = item.attrib['ph'] != ""
        if buffer_flag:
            item_type_xml.text = 'Buffer'
        else:
            item_type_xml.text = 'Precipitant'
        item_xml.append(item_type_xml)

        concentration = et.Element('concentration')
        conc_text = item.attrib['conc'].strip(' ')
        conc_text = conc_text.rstrip('0')
        conc_text = conc_text.rstrip('.')
        concentration.text = conc_text
        item_xml.append(concentration)

        if buffer_flag:
            ph = et.Element('pH')
            ph.text = item.attrib['ph']
            item_xml.append(ph)

        lid_xml = et.Element('stockLocalID')
        lid_high_xml = None
        if len(stock_lids_lst) == 1:
            lid_xml.text = str(stock_lids_lst[0])
        elif buffer_flag and len(stock_lids_lst) == 2:
            lid_high_xml = et.Element('highPHStockLocalID')
            lid1 = stock_lids_lst[0]
            lid2 = stock_lids_lst[1]

            assert lid_ph_dict[lid1] is not None
            assert lid_ph_dict[lid1] is not None

            if lid_ph_dict[lid1] < lid_ph_dict[lid2]:
                lid_xml.text = str(lid1)
                lid_high_xml.text = str(lid2)
            else:
                lid_xml.text = str(lid2)
                lid_high_xml.text = str(lid1)
        else:
            raise NotImplementedError()

        item_xml.append(lid_xml)
        if lid_high_xml is not None:
            item_xml.append(lid_high_xml)



        

        



     

tree = et.ElementTree(screen)
tree.write('test.xml', pretty_print=True)
exit()


    # Add the stock
