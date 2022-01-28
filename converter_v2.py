import src

from collections import defaultdict
import xml.etree.ElementTree as et

# Load all the object factories
chems_f = src.factories.ChemicalsFactory('chemicals.json','chemical_alias.json', 'chem_group_members.json')
stocks_f = src.factories.StocksFactory('stocks.json')
phcurve_f = src.factories.PhCurveFactory('ph_curves.json', 'ph_points.json')
design_f = src.factories.DesignFactory(chems_f)
recipe_f = src.factories.RecipeFactory(stocks_f)

# Read the design and recipe files
design = design_f.get_design_from_xml(design_xml_path = 'Shotgun.xml')
recipe = recipe_f.get_recipe_from_xml(recipe_xml_path = 'Shotgun_recipe.xml')

# Start contructing the rockmaker objects based upon the design and recipe
screen = src.objects.ScreenXml()

# Keep track of which chemicals and stocks have been used so far, so I only add the required ones to the ingredients
used_chem_stocks = defaultdict(set)

for well_id in design.wells:
    dw = design.wells[well_id]

    condition = src.objects.ConditionXml()

    for di in dw.items:
        # Find the stock(s) that will be used for this design item
        low_chem_id = None
        high_chem_id = None
        if phcurve_f.is_chem_curve(di.chemical.id):
            curve = phcurve_f.get_curve_by_chem_id(di.chemical.id)
            low_chem_id = curve.low_chem_id
            high_chem_id = curve.high_chem_id
        else:
            low_chem_id = di.chemical.id

        # Find the stocks for the chemicals in this well
        # High stock condition will not be hit if there is no high stock for this chemical so 
        # must initialise it
        high_stock_id = None
        for recipe_stock in recipe.stocks:
            if recipe_stock.stock.chem_id == low_chem_id and well_id in recipe_stock.wells:
                low_stock_id = recipe_stock.stock.id
            if recipe_stock.stock.chem_id == high_chem_id and well_id in recipe_stock.wells:
                high_stock_id = recipe_stock.stock.id


        condition_ingredient = src.objects.ConditionIngredientXml(
            item_class = di.item_class,
            concentration = di.concentration,
            ph = di.ph,
            local_id = low_stock_id,
            high_local_id = high_stock_id,
        )
        condition.add_ingredient(condition_ingredient)

        used_chem_stocks[di.chemical.id].add(low_stock_id)
        if high_stock_id is not None:
            used_chem_stocks[di.chemical.id].add(high_stock_id)

    screen.add_condition(condition)

    break

for chem_id in used_chem_stocks:
    chemical = chems_f.get_chem_by_id(chem_id)

    # Create the buffer data
    buffer_data = None
    if phcurve_f.is_chem_curve(chem_id):
        curve = phcurve_f.get_curve_by_chem_id(chem_id)
        points = [(x.ph, src.utils.frac2ratio(x.base_fraction)) for x in curve.points[1:]]
        buffer_data = src.objects.BufferDataXml(titration_points=points)
    else:
        if chemical.pka is not None:
            buffer_data = src.objects.BufferDataXml(pka = chemical.pka)

    stocks = src.objects.StocksXml()
    for stock_id in used_chem_stocks[chem_id]:
        stock = stocks_f.get_stock_by_id(stock_id)
        stocks.add_stock(
            src.objects.StockXml(
                local_id = stock.id,
                concentration = stock.conc,
                units = stock.units,
                use_as_buffer = stock.ph is not None and 'Buffer' in chemical.groups, # TODO need to be more rigorous for use as buffer??
                ph = stock.ph,
            )
        )


    # Create the stocks

    screen.add_ingredient(
        src.objects.IngredientXml(
            name = chemical.name,
            aliases = chemical.aliases,
            cas_number = chemical.cas,
            types = chemical.groups,
            buffer_data = buffer_data,
            stocks = stocks,
        )
    )



tree = et.ElementTree(screen.get_xml_element())
tree.write('test.xml')