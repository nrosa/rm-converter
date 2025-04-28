CHEM_GROUPS = {
    1: 'Protein',
    2: 'Salt',
    3: 'Polymer',
    4: 'Buffer',
    5: 'Organic',
    6: 'Additive',
    7: 'Ligand',
    8: 'Cryoprotectant',
    9: 'Precipitant',
    10: 'Oil',
    11: 'Acid',
    12: 'Detergent',
    13: 'Fundamental Mixtures',
}


BUFFER = 'Buffer'

SHRTNAME_LEN = 9

CONC_PREC = 1
VOL_PREC = 1
PH_PREC = 1


class WATER(object):
    barcode = '267'
    name = 'water'
    conc = 100
    units = 'v/v'
    viscosity = 3
    comment = 'Automatically generated'


VUNITS = 'ul'

PARTNUMBER_PREFIX = "CSIRO"

DEFAULT_COMMENT = ''
DEFAULT_DESC = ''

LAB_NAME = 'BCC'

# Recipe constants
PH_TOL = 0.2  # If two pH's are within this value of each other they are considered to be the same when finding possible stocks
# A pH must be within this distance from the pka for henderson-hasselbach to be used
HH_PH_PKA_MAX_DIFF = 1.5
# If a pka is within this distance from another pka then is it unsuitable for henderson-hasselbach
HH_PKA_MIN_SEP = 2.0

RM_COMMENT = """
Notice: ROCK MAKER XML schema  copyright (c)2006, 2007 by Formulatrix, Inc., www.formulatrix.com
For more information on this file format visit http://www.formulatrix.com/rmxml.shtml
This XML file is generated according to the ROCK MAKER XML schema. Formulatrix grants you the license to freely use,
generate and redistribute XML documents conforming to the ROCK MAKER XML schema PROVIDED
(1) you do not extend or modify the schema and
(2) this entire notice appears unmodified at the top of every file.
End of notice.
"""
