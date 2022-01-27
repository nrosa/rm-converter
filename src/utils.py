def wellname2id(name: str):
    well_id = (ord(name[0]) - ord('A'))*12 + int(name[1:])
    return well_id

def frac2ratio(base_frac: int):
    acid_frac = 100 - base_frac
    return acid_frac / base_frac