

class StockSubstitution():
    def __init__(self, context):
        ingredient_id_by_name = {}
        for (ingredient_id, ingredient) in context.ingredients.items():
            ingredient_id_by_name[ingredient.name] = ingredient_id

        for (ingredient, aliases) in context.ingredient_aliases.items():
            for alias in aliases:
                ingredient_id_by_name[alias] = ingredient

        CSIRO_stocks_for_ingredient = {}
        for (stock_id, ingredient_stock) in context.ingredient_stocks.items():
            ingredient = ingredient_stock.ingredient

            has_CSIRO_vendor_part_number = ingredient_stock.vendor_part_number.startswith(
                'CSIRO')
            in_BCC_namespace = context.ingredients[ingredient].name.in_BCC_namespace(
            )
            active = ingredient_stock.active

            if not (has_CSIRO_vendor_part_number and in_BCC_namespace and active):
                continue

            if not ingredient in CSIRO_stocks_for_ingredient:
                CSIRO_stocks_for_ingredient[ingredient] = {}
            CSIRO_stocks_for_ingredient[ingredient][stock_id] = ingredient_stock

        for (vendor_ingredient_id, vendor_ingredient) in context.ingredients.items():
            if vendor_ingredient.name.in_BCC_namespace():
                continue

            for CSIRO_name in vendor_ingredient.BCC_names():
                if not CSIRO_name in ingredient_id_by_name:
                    continue

                CSIRO_ingredient = ingredient_id_by_name[CSIRO_name]
                if not vendor_ingredient_id in CSIRO_stocks_for_ingredient:
                    CSIRO_stocks_for_ingredient[vendor_ingredient_id] = {}

                if CSIRO_ingredient in CSIRO_stocks_for_ingredient:
                    CSIRO_stocks_for_ingredient[vendor_ingredient_id] |= CSIRO_stocks_for_ingredient[CSIRO_ingredient]

        self.CSIRO_stocks_for_ingredient = CSIRO_stocks_for_ingredient
    def check(self, a, b, a_name, b_name, context):
        a = set(a)
        b = set(b)
        pathological = a.intersection(b)
        pathological_stocks = [
            context.ingredient_stocks[stock_id] for stock_id in pathological]
        pathological_ingredients = [
            context.ingredients[context.ingredient_stocks[stock_id].ingredient] for stock_id in pathological]
        pathological_diagnostics = [
            f'stock id={stock_id} vendor part number="{stock.vendor_part_number}" vendor "{stock.vendor_name}" for {ingredient.name}' for (stock_id, stock, ingredient) in zip(pathological, pathological_stocks, pathological_ingredients)]
        if len(pathological) > 0:
            raise Exception(
                f'found {len(pathological)} ({pathological_diagnostics}) stocks used as both {a_name} and {b_name} stocks in same screen')
        
        
    def __call__(self, stock):
        