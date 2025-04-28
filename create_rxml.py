from .src.factories import xtaltrak
import argparse
import os
from lxml import etree
import pathlib
import sys
import re

from .src.factories import convert

current_dir = pathlib.Path(__file__).parent.resolve()
sys.path.append(str(current_dir))

not_allowed_in_windows_filename = re.compile(r'[\/:*?"<>|]')


def rockmaker_filename(screen_name):
    if not isinstance(screen_name, pathlib.PurePath):
        prefix = pathlib.PurePath(
            re.sub(not_allowed_in_windows_filename, ' ', screen_name))
    else:
        prefix = screen_name

    return pathlib.PurePath(f'{prefix}_RockMaker.xml')


class FactoriesJSON:
    def __init__(self, data_dir=current_dir / "data"):
        # Load all the object factories
        self.chems = xtaltrak.ChemicalsFactory(
            os.path.join(data_dir, 'chemicals.json'),
            os.path.join(data_dir, 'chemical_alias.json')
        )
        self.stocks = xtaltrak.StocksFactory(
            os.path.join(data_dir, 'stocks.json'),
            self.chems
        )
        self.phcurve = xtaltrak.PhCurveFactory(
            os.path.join(data_dir, 'ph_curves.json'),
            os.path.join(data_dir, 'ph_points.json'),
            self.chems
        )
        self.design = xtaltrak.DesignFactory(self.chems)
        self.recipe = xtaltrak.RecipeFactory(self.stocks)


class FactoriesRM:
    pass


def to_rm_xml(*, factory, design_xo, recipe_xo=None, as_string=True, include_aliases=False):

    stocks_f = factory.stocks
    phcurve_f = factory.phcurve
    design_f = factory.design
    recipe_f = factory.recipe

    # Read the design and recipe files
    design = design_f.get_design_from_xml_object(design_xo)
    recipe = None
    if recipe_xo is not None:
        recipe = recipe_f.get_recipe_from_xml_object(recipe_xo)

    screen = convert.design2screen(
        design=design, recipe=recipe, stocks_f=stocks_f, phcurve_f=phcurve_f, require_exact_ph=True, include_aliases=include_aliases)

    return screen.to_xml(as_string=as_string)


def write_rm_xml_file(*, output_xml, **kwargs):
    xmlstr = to_rm_xml(**kwargs)
    with open(output_xml, "w") as f:
        f.write(xmlstr)


def main(*, design_xml, recipe_xml, output_xml):
    # Read in the xml files
    design_xo = etree.parse(design_xml).getroot()
    recipe_xo = None
    if recipe_xml is not None:
        recipe_xo = etree.parse(recipe_xml).getroot()

    write_rm_xml_file(
        output_xml=output_xml,
        factory=FactoriesJSON(),
        design_xo=design_xo,
        recipe_xo=recipe_xo,
    )


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='RockMaker Recipe converter.')

    # Dataset parameters
    parser.add_argument('--design-xml', type=str, required=True)
    parser.add_argument('--recipe-xml', type=str, default=None)
    parser.add_argument('--output-xml', type=str,
                        default='rockmaker_design.xml')

    args = parser.parse_args()

    main(design_xml=args.design_xml,
         recipe_xml=args.recipe_xml,
         output_xml=args.output_xml)
