import src

from collections import defaultdict
import warnings
import os

import xml.etree.ElementTree as et
from xml.dom import minidom

import argparse



def main(args):

    # Load rxml into objects
    screen = src.factories.formtrix.screen_from_rxml('Shotgun_rxml.xml')

    # Get stocks per well

    # Calculate volumes

    # Write XML

    exit()

    
    xmlstr = minidom.parseString(et.tostring(screen.get_xml_element())).toprettyxml(indent="   ")
    with open(args.output_xml, "w") as f:
        f.write(xmlstr)

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='RockMaker Recipe converter.')

    # Dataset parameters
    parser.add_argument('--rxml', type=str, required=True)
    parser.add_argument('--output-xml', type=str, default='xtaltrak_recipe.xml')
    parser.add_argument('--data-dir', type=str, default='data')

    parser.add_argument('--volume', type=float, default=1500, help='volume per well in uL')

    args = parser.parse_args()

    main(args)