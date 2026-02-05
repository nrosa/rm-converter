class LocalIdFactory(object):
    def __init__(self):
        # Start the local IDs at 1
        self.count = 1
        self.cache = dict()

    def get_local_id(self, chem_id: int, stock_id: int):
        if stock_id is None:
            return None
        assert isinstance(chem_id, int)
        assert isinstance(stock_id, int)
        # Local IDs are handed out to each chem_id, stock_id pair
        if (chem_id, stock_id) not in self.cache:
            self.cache[(chem_id, stock_id)] = self.count
            self.count = self.count + 1
        return self.cache[(chem_id, stock_id)]
