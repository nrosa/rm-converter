import src
import src.objects.xtaltrak_recipe_xml as xtal_xml
from collections import defaultdict
import warnings
import os

import xml.etree.ElementTree as et
from xml.dom import minidom

import argparse



def main(args):

    # Load rxml into objects
    screen = src.factories.formtrix.screen_from_rxml(args.rmxml)

    # Calculate volumes
    screen.add_recipe_volume(args.volume)

    # Convert to xtaltrak recipe object

    # Create stocks
    stocks = xtal_xml.Stocks()
    for ftrix_stock in screen.get_stocks():
        stocks.add_stock(
            src.factories.formtrix.to_xtaltrak_recipe_stock(ftrix_stock)
        )
    

    wells = xtal_xml.Wells(args.volume)
    for ftrix_stock in screen.get_stocks():
        wells.add_stock(
            src.factories.formtrix.to_xtaltrak_recipe_wellstock(ftrix_stock)
        )

    plate = xtal_xml.Plate(wells)

    # Create sourceplates
    description = ''
    sourceplate = xtal_xml.SourcePlate(description, stocks, plate)
    sourceplates = xtal_xml.SourcePlates()
    sourceplates.add_sourceplate(sourceplate)
    name = ''.join(args.rmxml.split('.')[:-1])
    job = xtal_xml.Job(name, sourceplates)

    # Add water ingredient
    # [well_id: volume]
    global_usage = defaultdict(float)
    for ftrix_stock in screen.get_stocks():
        for well_id in ftrix_stock.usages:
            global_usage[well_id] += ftrix_stock.usages[well_id]

    # invert global usages so it reflects water usage
    for well_id in global_usage:
        global_usage[well_id] = round(args.volume - global_usage[well_id], 1)
    # Delete zero water entries
    global_usage = {k:round(v,1) for k,v in global_usage.items() if round(v,1) > 0}
    # Add water stock
    stocks.add_stock(xtal_xml.Stock(
        barcode=src.constants.WATER.barcode,
        comments=src.constants.WATER.comment,
        conc=src.constants.WATER.conc,
        count=len(global_usage),
        cunits=src.constants.WATER.units,
        name=src.constants.WATER.name,
        viscosity=src.constants.WATER.viscosity,
        volume=sum([global_usage[x] for x in global_usage]),
        vunits=src.constants.VUNITS,
    ))
    # Add water wells
    water_well_stock = xtal_xml.WellStock(
        barcode=src.constants.WATER.barcode,
        comments=src.constants.WATER.comment,
        conc=src.constants.WATER.conc,
        cunits=src.constants.WATER.units,
        name=src.constants.WATER.name,
        viscosity=src.constants.WATER.viscosity,
    )
    for well_id in sorted(list(global_usage.keys())):
        water_well_stock.add_well(xtal_xml.Well(
            src.utils.wellid2name(well_id),
            global_usage[well_id],
            src.constants.VUNITS,
        ))
    wells.add_stock(water_well_stock)



    # Write XML
    xmlstr = minidom.parseString(et.tostring(job.get_xml_element())).toprettyxml(indent="   ")
    with open(args.output_xml, "w") as f:
        f.write(xmlstr)

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='RockMaker Recipe converter.')

    # Dataset parameters
    parser.add_argument('--rmxml', type=str, required=True)
    parser.add_argument('--output-xml', type=str, default='xtaltrak_recipe.xml')
    parser.add_argument('--volume', type=float, default=1500, help='volume per well in uL')

    args = parser.parse_args()

    main(args)