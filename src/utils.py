from .config import constants

import math


def wellname2id(name: str) -> int:
    well_id = (ord(name[0]) - ord('A'))*12 + int(name[1:])
    return well_id


def wellid2name(well_id: int) -> str:
    assert (well_id > 0)
    well_idx = well_id - 1
    return chr(ord('A') + well_idx//12) + str(well_idx % 12 + 1)


def frac2ratio(base_frac: int) -> float:
    acid_frac = 100 - base_frac
    return acid_frac / base_frac


def trim_shortname(shortname: str) -> str:
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
    if stock is None:
        return None
    return stock.short_name


def get_shortname_from_aliases(aliases) -> str:
    return trim_shortname(sorted(aliases, key=lambda x: len(x))[0])


def prefix_str(prefix, s, do_adjust):
    if not do_adjust or s.startswith(prefix):
        return s
    return prefix + s


def suffix_str(s, suffix, do_adjust):
    if not do_adjust or s.endswith(suffix):
        return s
    return s + suffix


def get_shortname_from_lid_name(lid_name):
    '''
    eg. MnCl2 (0.1M)
    bicine pH 7.4 (1M)
    '''
    shortname = lid_name
    if shortname is None:
        return None

    shortname = shortname.split(' (')[0]

    if 'pH' in shortname:
        shortname = shortname.split('pH')[0]

    # Remove all whitespace
    shortname = shortname.replace(' ', '')

    return trim_shortname(shortname.strip())


def convertstr(item):
    if item is not None:
        if isinstance(item, float):
            return f'{item:.2f}'
        # Default case
        return str(item)
    return ''


def partnumber_to_barcode(partnumber):
    if len(partnumber) >= 6 and constants.PARTNUMBER_PREFIX + "-" == partnumber[:6]:
        return partnumber[6:]
    return ''


def _is_tacsimate(name: str):
    import re
    x = re.search("^tacsimate", name)
    return x != None


def henderson_hasselbach_mix(pka: float, low_ph: float, high_ph: float, desired_ph: float) -> float:
    """
    Calculates the fraction of the buffer component at the lower pH needed to achieve the desired pH,
    based on the Henderson-Hasselbalch equation.
    """
    exp_low = math.pow(10, low_ph - pka)
    exp_high = math.pow(10, high_ph - pka)
    exp_desired = math.pow(10, desired_ph - pka)

    part_low1 = 1 / (1 + exp_low)
    part_high1 = 1 / (1 + exp_high)
    part_low2 = 1 / (1 + 1 / exp_low)
    part_high2 = 1 / (1 + 1 / exp_high)

    frac_num = (exp_desired * part_high1 - part_high2)
    frac_denom = (part_low2 - part_high2 -
                  exp_desired * (part_low1 - part_high1))
    fraction_low = frac_num / frac_denom

    return fraction_low
