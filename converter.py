import src

from collections import defaultdict
import warnings
import os

import xml.etree.ElementTree as et
from xml.dom import minidom

import argparse


def main(args):

    # Load all the object factories
    chems_f = src.factories.ChemicalsFactory(
        os.path.join(args.data_dir, 'chemicals.json'),
        os.path.join(args.data_dir, 'chemical_alias.json'),
        os.path.join(args.data_dir, 'chem_group_members.json'),
    )
    stocks_f = src.factories.StocksFactory(
        os.path.join(args.data_dir, 'stocks.json'),
        )
    phcurve_f = src.factories.PhCurveFactory(
        os.path.join(args.data_dir, 'ph_curves.json'),
        os.path.join(args.data_dir, 'ph_points.json'),
        stocks_f
    )
    design_f = src.factories.DesignFactory(chems_f)
    recipe_f = src.factories.RecipeFactory(stocks_f)
    lid_f = src.factories.LocalIdFactory()

    # Read the design and recipe files
    design = design_f.get_design_from_xml(design_xml_path = args.design_xml)
    recipe = recipe_f.get_recipe_from_xml(recipe_xml_path = args.recipe_xml)

    # Start contructing the rockmaker objects based upon the design and recipe
    screen = src.objects.ScreenXml()

    # Keep track of which chemicals and stocks have been used so far, so I only add the required ones to the ingredients
    # Key is chem_id
    ingredient_dict = dict() # dict[objects.Ingredient]

    for well_id in design.wells:
        # if well_id != 45 and well_id != 42: #and well_id != 77:#77:
        #     continue
        dw = design.wells[well_id]

        condition = src.objects.ConditionXml()

        for di in dw.items:
            # Create ingredient object
            if di.chemical.id not in ingredient_dict:
                ingredient_dict[di.chemical.id] = src.objects.Ingredient(di.chemical)
            ingredient = ingredient_dict[di.chemical.id]

            # Add the type context for this Ingredient
            ingredient.add_type(di.item_class)


            # Initialise the stock ids for this condition ingredient
            low_stock_id = None
            high_stock_id = None

            well_recipe_stocks = recipe.get_stocks_for_well(well_id)

            if di.item_class == src.constants.BUFFER:
                di_chem_ids = list()
                if phcurve_f.is_chem_curve(di.chemical.id):
                    curve = phcurve_f.get_curve_by_chem_id(di.chemical.id)
                    if curve.low_chem_id == curve.high_chem_id:
                        di_chem_ids = (curve.low_chem_id,)
                    else:
                        di_chem_ids = (curve.low_chem_id, curve.high_chem_id)
                else:
                    di_chem_ids = (di.chemical.id,)

                # Find the stocks for these chemicals from the recipe
                di_stock_ids = list()
                
                for chem_id in di_chem_ids:
                    di_stock_ids += [x.stock.id for x in well_recipe_stocks if x.stock.chem_id == chem_id]

                assert len(di_stock_ids) == 1 or len(di_stock_ids) == 2

                if len(di_stock_ids) == 1:
                    low_stock_id = di_stock_ids[0]
                else:
                    stock0 = stocks_f.get_stock_by_id(di_stock_ids[0])
                    stock1 = stocks_f.get_stock_by_id(di_stock_ids[1])
                    if stock0.ph < stock1.ph:
                        low_stock_id = di_stock_ids[0]
                        high_stock_id = di_stock_ids[1]
                    else:
                        low_stock_id = di_stock_ids[1]
                        high_stock_id = di_stock_ids[0]

                ingredient.add_stock(low_stock_id, True)
                if high_stock_id is not None:
                    ingredient.add_stock(high_stock_id, True)

            else:
                di_stock_ids = [x.stock.id for x in well_recipe_stocks if x.stock.chem_id == di.chemical.id]
                assert len(di_stock_ids) == 1
                low_stock_id = di_stock_ids[0]

                ingredient.add_stock(low_stock_id, False)
            
            low_lid = lid_f.get_local_id(di.chemical.id, low_stock_id)
            high_lid = lid_f.get_local_id(di.chemical.id, high_stock_id)

            condition_ingredient = src.objects.ConditionIngredientXml(
                item_class = di.item_class,
                concentration = di.concentration,
                ph = di.ph,
                local_id = low_lid,
                high_local_id = high_lid,
            )
            condition.add_ingredient(condition_ingredient)

            # used_chem_stocks[di.chemical.id].add(low_stock_id)
            # if high_stock_id is not None:
            #     used_chem_stocks[di.chemical.id].add(high_stock_id)

        screen.add_condition(condition)


    for chem_id in ingredient_dict:
        ingredient = ingredient_dict[chem_id]

        chemical = chems_f.get_chem_by_id(chem_id)

        # Create the buffer data
        buffer_data = None
        # Only create the bufferdata if the ingredient is used in a buffer context
        if ingredient.is_buffer():
            if phcurve_f.is_chem_curve(chem_id):
                curve = phcurve_f.get_curve_by_chem_id(chem_id)
                points = [(x.ph, x.acid_fraction) for x in curve.points]
                buffer_data = src.objects.BufferDataXml(titration_points=points)
            else:
                if chemical.pka is not None:
                    if chemical.pka_warn:
                        warnings.warn(f'Warning: Chemical {chemical.name} has multiple pKas, using {chemical.pka}')
                    buffer_data = src.objects.BufferDataXml(pka = chemical.pka)


        stocks = src.objects.StocksXml()
        for stock_id, use_as_buffer in ingredient.stocks:
            stock = stocks_f.get_stock_by_id(stock_id)
            stocks.add_stock(
                src.objects.StockXml(
                    local_id = lid_f.get_local_id(chem_id, stock.id),
                    stock_id = stock.id,
                    concentration = stock.conc,
                    units = stock.units,
                    use_as_buffer = use_as_buffer,
                    ph = stock.ph,
                )
            )


        # Create the stocks
        if chemical.cas is None:
            warnings.warn(f'Warning: Chemical {chemical.name} has no CAS, this will need to be resolved when importing into RockMaker')

        shortname = src.utils.get_shortname_from_stocklid(chemical, stocks_f)
        if shortname is None:
            if len(chemical.aliases) > 0:
                src.utils.get_shortname_from_aliases(chemical.aliases)
            else:
                shortname = name[:constants.SHRTNAME_LEN] if len(chemical.name) > constants.SHRTNAME_LEN else chemical.name

        screen.add_ingredient(
            src.objects.IngredientXml(
                name = chemical.name,
                shortname = shortname,
                aliases = chemical.aliases if args.include_aliases else [],
                cas_number = chemical.cas if chemical.cas is not None else '-1',
                types = ingredient.types,
                buffer_data = buffer_data,
                stocks = stocks,
            )
        )


    # tree = et.ElementTree()

    xmlstr = minidom.parseString(et.tostring(screen.get_xml_element())).toprettyxml(indent="   ")
    with open(args.output_xml, "w") as f:
        f.write(xmlstr)

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='RockMaker Recipe converter.')

    # Dataset parameters
    parser.add_argument('--recipe-xml', type=str, required=True)
    parser.add_argument('--design-xml', type=str, required=True)
    parser.add_argument('--output-xml', type=str, default='rockmaker_design.xml')
    parser.add_argument('--data-dir', type=str, default='data')

    parser.add_argument('--include-aliases', action='store_true')

    args = parser.parse_args()

    main(args)