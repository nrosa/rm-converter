# import src.objects as objects
# import src.factories as factories
from . import constants

def wellname2id(name: str):
    well_id = (ord(name[0]) - ord('A'))*12 + int(name[1:])
    return well_id

def wellid2name(well_id: int):
    return chr(ord('A') + well_id//12)+ str(well_id%12 + 1)

def frac2ratio(base_frac: int):
    acid_frac = 100 - base_frac
    return acid_frac / base_frac

def trim_shortname(shortname):
    if len(shortname) > constants.SHRTNAME_LEN:
        shortname = shortname[:constants.SHRTNAME_LEN]
    return shortname

def get_shortname_from_stocklid(
    chemical,
    sf
) -> str:
    '''
    eg. MnCl2 (0.1M)
    bicine pH 7.4 (1M)
    '''
    stock = sf.get_first_stock_by_chemid(chemical.id)
    if stock is None: return None
    shortname = stock.lid_name
    if shortname is None: return None

    shortname = shortname.split(' (')[0]

    if 'pH' in shortname:
        shortname = shortname.split('pH')[0]

    # Remove all whitespace
    shortname = shortname.replace(' ','')

    return trim_shortname(shortname.strip())

def get_shortname_from_aliases(aliases) -> str:
    return trim_shortname(sorted(aliases, key=lambda x: len(x))[0])
        

