from lxml import etree
import argparse
from pathlib import Path

from .src import objects
from .src.factories import rockmaker
from .src.factories.convert import rmscreen2xtrecipe


screen_from_rxml_dom = rockmaker.screen_from_rxml_dom


def convert_screen(*, screen: objects.rockmaker.Screen, volume, output_xml=None, require_exact_ph):
    # Calculate volumes
    screen.add_recipe_volume(volume, require_exact_ph=require_exact_ph)
    sp = rmscreen2xtrecipe(screen)
    sp.add_water()

    # Write XML
    root = sp.get_xml_element()
    etree.indent(root, space="   ")
    xmlstr = etree.tostring(root, xml_declaration=True,
                            pretty_print=True, encoding='utf-8').decode()
    if not output_xml is None:
        with open(output_xml, "w") as f:
            f.write(xmlstr)

    return xmlstr


def main(*, rmxml, volume, output_xml=None, require_exact_ph):
    if isinstance(rmxml, str):
        rmxml = Path(rmxml)

    # Load rxml into objects
    screen = rockmaker.screen_from_rxml_file(rmxml, name=rmxml.stem)

    return convert_screen(screen=screen, volume=volume, output_xml=output_xml, require_exact_ph=require_exact_ph)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='RockMaker Recipe converter.')

    # Dataset parameters
    parser.add_argument('--rmxml', type=str, required=True)
    parser.add_argument('--output-xml', type=str,
                        default='xtaltrak_recipe.xml')
    parser.add_argument('--volume', type=float, default=1000,
                        help='volume per well in uL')
    parser.add_argument('--require-exact-ph',
                        action=argparse.BooleanOptionalAction, default=True)
    args = parser.parse_args()

    main(
        rmxml=args.rmxml,
        volume=args.volume,
        output_xml=args.output_xml,
        require_exact_ph=args.require_exact_ph,
    )
