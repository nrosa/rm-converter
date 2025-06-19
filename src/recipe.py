from .exceptions import RecipeError
from .utils import henderson_hasselbach_mix
from .factories.bases import _StocksFactory, _PhCurveFactory
from .config.constants import PH_TOL, HH_PH_PKA_MAX_DIFF
from .objects.xtaltrak import Stock, DesignItem, DesignWell
import math
from dataclasses import dataclass
from typing import List, Tuple, Optional
from itertools import product

# TODO Temporarily hardcoded stock ids
stockaid_avail = {3520, 1099, 110, 2440, 3601, 371, 3660, 3666, 3723, 2143, 1377, 3401, 190, 1369, 1037, 128, 903, 2702, 3066, 826, 1387, 1382, 2542, 3022, 3021, 2540, 3132, 4244, 4245, 4260, 4002, 4001, 1939, 4240, 844, 4340, 4341, 4360, 3863, 4380, 220, 1655, 219, 1362, 3121, 201, 4440, 3122, 1652, 243, 1386, 1761, 2781, 1432, 200, 315, 3740, 2363, 271, 198, 3669, 194, 1380, 146, 2606, 1394, 908, 1375, 3662, 2044, 1979, 1777, 475, 1032, 1031, 183, 291, 292, 4160, 4460, 2520, 208, 1201, 4481, 1373, 4220, 140, 1696, 2763, 622, 805, 1240, 445, 258, 1899, 1900, 196, 4500, 4520, 148, 4600, 2765, 1258, 3260, 4161, 1532, 370, 1320, 262, 1262, 938, 209, 395, 179, 830, 2800, 1378, 1379, 212, 1227, 3460, 217, 1223, 2340, 1006, 2141, 199, 4480, 2620, 273, 1672, 1265, 206, 540, 3129, 3126, 3125, 3127, 1038, 362, 1389, 299, 3131, 3124, 202, 1492, 1451, 123, 1693, 1673, 1692, 1779, 2764, 1715, 3880, 621, 2142, 3940, 940, 218, 3123, 2602, 2400, 3128, 2220, 1121, 1239, 945, 363, 234, 303, 173, 2421, 2019, 1393, 1424, 1081, 349, 1281, 1282, 2280, 825, 3864, 2200, 3743, 1361, 1010, 1011, 1260, 1363, 1266, 829, 306, 471, 1400, 626, 2160, 835, 2541, 236, 1181, 310, 1252, 1253, 138, 318, 2600, 322, 323, 2601, 1372, 1515, 121, 1244, 3024, 3025, 2607, 204, 181, 2605, 2820, 3860, 1302, 3700, 3744, 311, 117, 3641, 166, 2941, 4711, 4710, 4361, 1254, 1079, 470, 4809, 1230, 4750, 4703, 4849, 4872, 4870, 4751, 4871, 4869, 4789, 4873, 4909, 4729, 4769, 4647, 4704, 4702, 2762, 2780, 4949, 1028, 1697, 3440, 36, 4706, 418, 108, 224, 260, 293, 350, 134, 3902, 624, 4080, 520, 3721, 1259, 4241, 1007, 3720, 1778, 2861, 4020, 4180, 1431, 1592, 205, 3130, 1041, 1839, 2300, 1059, 744, 1760, 4889, 1340, 1430, 1759, 804, 2900, 1533, 1222, 789, 1383, 421, 2420, 3420, 1920, 246, 824, 444, 62, 1371, 476, 1376, 623, 1517, 4, 1039, 1699, 1392, 1119, 4714, 4713, 1246, 450, 907, 2320, 895, 211, 1758, 4140, 899, 1713, 309, 3120, 14, 1280, 320, 1780, 207, 1959, 284, 125, 43, 2360, 946, 3621, 3780, 1999}


@dataclass
class StockFrac:
    stock: Stock
    frac: float
    high_stock: Stock = None
    high_frac: float = None


def compare_ph(ph1: float, ph2: float, require_exact_ph: bool = False) -> bool:
    if require_exact_ph:
        return ph1 == ph2
    else:
        return abs(ph1-ph2) < PH_TOL

def prefer_dispense(dispense, best_dispense) -> bool:
    """
    Returns True if dispense is better than best_dispense.
    A dispense is better if it has a higher value at the first index where they differ.
    If they are equal, returns False.
    """
    for i in range(min(len(dispense), len(best_dispense))):
        if dispense[i] > best_dispense[i]:
            return True
        elif dispense[i] < best_dispense[i]:
            return False
    return False


def pick_stocks_for_well(
    dw: DesignWell,
    stocks_f: _StocksFactory,
    phcurve_f: _PhCurveFactory,
    require_exact_ph: bool,
    return_dispenses: bool = False,
) -> List[Tuple[Stock, Optional[Stock]]]:
    possible_stocks = get_possible_stocks(
        dw, stocks_f, phcurve_f, require_exact_ph)
    
    num_factors = len(dw.items)

    # Check if there are any factors that have no possible stocks
    for i, x in enumerate(possible_stocks):
        if len(x) == 0:
            raise RecipeError(f'{dw.items[i]} has no possible stocks.')

    idxs = [0]*num_factors
    best_dispense = [-1]
    best_stocks = None

    for idxs in product(*[range(len(x)) for x in possible_stocks]):
        # Calculate dispense values for the current combination of stocks
        dispenses = []
        for stocks, idx in zip(possible_stocks, idxs):
            sv1 = stocks[idx]
            dispenses.append(sv1.frac)
            if sv1.high_frac is not None:
                dispenses.append(sv1.high_frac)

        # Do we overflow
        if sum(dispenses) > 1:
            continue

        dispenses.sort()
        if prefer_dispense(dispenses, best_dispense):
            # If this dispense is better than the best dispense, update best_dispense and best_stocks
            best_dispense = dispenses
            best_stocks = []
            for k in range(num_factors):
                sv2 = possible_stocks[k][idxs[k]]
                best_stocks.append((sv2.stock, sv2.high_stock))

    if best_stocks is None:
        raise RecipeError('Could not generate recipe.')
    if return_dispenses:
        return best_stocks, best_dispense
    return best_stocks


def get_possible_stocks(
    dw: DesignWell,
    stocks_f: _StocksFactory,
    phcurve_f: _PhCurveFactory,
    require_exact_ph: bool,
    filter_unavailable: bool = True,
) -> list:
    # TODO There are dispense values that are very close to zero but negative
    all_possible_stocks = []
    for di in dw.items:
        possible_stocks = []
        # TODO Name instead of id?
        factor_stocks = stocks_f.get_stocks_by_chemid(di.chemical.id)
        # Filter out stocks that are not available
        if filter_unavailable:
            factor_stocks = [fs for fs in factor_stocks if fs.available and fs.id in stockaid_avail]
        if di.ph is None:
            possible_stocks += find_exact_match(di,
                                                factor_stocks, require_exact_ph)
        else:
            # Henderson Hasselbach
            possible_stocks += find_hh_stocks(di, factor_stocks)
            possible_stocks += find_phcurve_stocks(di, stocks_f, phcurve_f)
            # If a stock pair can't be found by mixing buffers fallback to an exact match
            # Rockmaker complains if a buffer only has one stock so this is only done if stocks cant
            # be found by another means
            if len(possible_stocks) == 0:
                possible_stocks += find_exact_match(di,
                                                    factor_stocks, require_exact_ph)
        
        all_possible_stocks.append(possible_stocks)
    return all_possible_stocks


def find_exact_match(
        di: DesignItem,
        factor_stocks: List[Stock],
        require_exact_ph: bool,
) -> List[Stock]:
    possible_stocks = []
    for fs in factor_stocks:
        if compare_ph(fs.ph, di.ph, require_exact_ph) and fs.conc > di.concentration:
            possible_stocks.append(StockFrac(
                fs, di.concentration / fs.conc))
    return possible_stocks


def find_hh_stocks(
    di: DesignItem,
    factor_stocks: List[Stock]
) -> List[Stock]:
    possible_stocks = []
    # Find if there is a pka that can be used for HH
    # TODO Currently doesn't check how close the pkas are together
    hh_pka = None
    for pka in di.chemical.pkas:
        if abs(pka - di.ph) < HH_PH_PKA_MAX_DIFF:
            hh_pka = pka

    if hh_pka is not None:
        low_stocks = []
        for fs in factor_stocks:
            if fs.conc > di.concentration:
                if fs.ph is not None and abs(fs.ph - hh_pka) < HH_PH_PKA_MAX_DIFF and fs.ph <= di.ph:
                    low_stocks.append(fs)

        for fs in factor_stocks:
            if fs.ph is not None and abs(fs.ph - hh_pka) < HH_PH_PKA_MAX_DIFF and fs.ph >= di.ph:
                # Find the matching low ph stock
                for low_fs in low_stocks:
                    if low_fs.conc == fs.conc and low_fs.units == fs.units and low_fs.ph < fs.ph:
                        low_frac = henderson_hasselbach_mix(
                            hh_pka, low_fs.ph, fs.ph, di.ph)
                        cond_frac = di.concentration / low_fs.conc
                        possible_stocks.append(StockFrac(
                            stock=low_fs,
                            frac=cond_frac * low_frac,
                            high_stock=fs,
                            high_frac=cond_frac * (1-low_frac)
                        ))
    return possible_stocks


def find_phcurve_stocks(
        di: DesignItem,
        stocks_f: _StocksFactory,
        phcurve_f: _PhCurveFactory,
):
    possible_stocks = []
    # TODO Name instead of id?
    curve = phcurve_f.get_curve_by_chem_id(di.chemical.id)
    if curve is not None and curve.low_ph is not None and curve.high_ph is not None and curve.low_ph <= di.ph and curve.high_ph >= di.ph:
        low_curve_stocks = stocks_f.get_stocks_by_chemid(curve.low_chem.id)
        high_curve_stocks = stocks_f.get_stocks_by_chemid(curve.high_chem.id)
        # Check that there are points in the curve
        if len(curve.points) > 0:
            # Find the closest ph point in the curve to the desired ph
            min_dist = abs(di.ph-curve.points[0].ph)
            best_point = curve.points[0]
            for point in curve.points:
                dist = abs(di.ph - point.ph)
                if dist < min_dist:
                    min_dist = dist
                    best_point = point

            for lcs in low_curve_stocks:
                # Can this stock be used
                if lcs.conc > di.concentration and lcs.ph == curve.low_ph:
                    cond_frac = di.concentration / lcs.conc
                    # Find a matching high ph stock
                    for hcs in high_curve_stocks:
                        if hcs.conc == lcs.conc and hcs.ph == curve.high_ph:
                            # Transform the percentage in PhPoint to a fraction
                            possible_stocks.append(StockFrac(
                                stock=lcs,
                                frac=cond_frac*best_point.acid_fraction / 100,
                                high_stock=hcs,
                                high_frac=cond_frac*best_point.base_fraction / 100
                            ))
    return possible_stocks
