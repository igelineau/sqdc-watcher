class Product:
    def __init__(self, product_data):
        self.data = product_data
        self.id = self.data['id']

    def has_specifications(self):
        return self.find_variant_with_specs() is not None

    def get_specification(self, key):
        variant_with_spec = self.find_variant_with_specs()
        return '' if variant_with_spec is None else variant_with_spec['specifications'].get(key)

    def find_variant_with_specs(self):
        return next((v for v in self.data['variants'] if 'specifications' in v), None)

    def is_in_stock(self):
        return self.data['in_stock'] and len(self.get_variants_in_stock()) > 0

    def get_variants_in_stock(self):
        return [v for v in self.data['variants'] if v['in_stock']]

    def get_property(self, name) -> str:
        return self.data[name]
