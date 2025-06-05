from .exceptions import RecipeError
from .utils import henderson_hasselbach_mix
from .factories.bases import _StocksFactory, _PhCurveFactory
from .config.constants import PH_TOL, HH_PH_PKA_MAX_DIFF
from .objects.xtaltrak import Stock, DesignItem, DesignWell
import math
from dataclasses import dataclass
from typing import List, Tuple, Optional
from itertools import product


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
) -> List[Tuple[Stock, Optional[Stock]]]:
    possible_stocks = get_possible_stocks(
        dw, stocks_f, phcurve_f, require_exact_ph)
    
    num_factors = len(dw.items)

    # Check if there are any factors that have no possible stocks
    for i, x in enumerate(possible_stocks):
        if len(x) == 0:
            raise RecipeError(f'{dw.items[i]} has no possible stocks.')

    num_stock_combinations = math.prod([len(x) for x in possible_stocks])
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
            factor_stocks = [fs for fs in factor_stocks if fs.available]
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
