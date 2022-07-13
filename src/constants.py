CHEM_GROUPS = {
    1:'Protein',
    2:'Salt',
    3:'Polymer',
    4:'Buffer',
    5:'Organic',
    6:'Additive',
    7:'Ligand',
    8:'Cryoprotectant',
    9:'Precipitant',
    10:'Oil',
    11:'Acid',
    12:'Detergent',
    13:'Fundamental Mixtures',
}


BUFFER = 'Buffer'

SHRTNAME_LEN = 6


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