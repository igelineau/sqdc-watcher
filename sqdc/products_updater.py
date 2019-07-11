import logging
import random
import string
import time
from datetime import datetime
from typing import List, Dict

from babel.dates import format_timedelta
from bs4 import BeautifulSoup

from sqdc import SqdcStore
from sqdc.dataobjects.product import Product
from sqdc.dataobjects.product_variant import ProductVariant
from sqdc.formatter import SqdcFormatter
from sqdc.logic.product_calculator import find_by_id
from sqdc.logic.product_history_analyzer import ProductHistoryAnalyzer
from sqdc.sqdc_client import SqdcClient

DEFAULT_LOCALE = 'en-CA'
DOMAIN = 'https://www.sqdc.ca'
BASE_URL = DOMAIN + '/' + DEFAULT_LOCALE

SLACK_API_URL = 'https://slack.com/api'

log = logging.getLogger(__name__)


class ProductsUpdater:
    store: SqdcStore
    sqdc_client: SqdcClient

    def __init__(self, store: SqdcStore):
        self.store = store
        self.sqdc_client = SqdcClient()
        self.use_mocked_variants_in_stock = False

    def get_products(self, cached_products: List[Product], max_pages: int = 999999) -> List[Product]:
        start_time = time.time()

        products = cached_products or self.fetch_all_products_summary(max_pages=max_pages)
        self.populate_products_variants(products, products_cache_used=bool(cached_products))

        elapsed = format_timedelta(time.time() - start_time, granularity='millisecond')
        log.info(f'Website parsing - COMPLETED in {elapsed}')

        return products

    def fetch_all_products_summary(self, max_pages: int):
        page = 1
        has_reached_end = False
        products = []
        while not has_reached_end and page <= max_pages:
            products_html = self.sqdc_client.get_product_result_page_html(page)
            products_in_page = self.parse_products_html(products_html)
            has_reached_end = len(products_in_page) == 0
            if not has_reached_end:
                page += 1
            products += products_in_page
        log.info(f'Fetched {len(products)} from SQDC API ({page - 1})')
        self.store.update_last_scan_timestamp(datetime.now())

        return products

    @staticmethod
    def parse_products_html(raw_html: string):
        soup = BeautifulSoup(raw_html, 'html.parser')
        product_tags = soup.select('div.product-tile')
        products = []
        for ptag in product_tags:
            title_anchor = ptag.select_one('a[data-qa="search-product-title"]')
            title = title_anchor.contents[0]
            url = DOMAIN + title_anchor['href']
            try:
                brand_tag = ptag.select_one('div[class="js-equalized-brand"]')
                brand = "" if len(brand_tag.contents) == 0 else brand_tag.contents[0]
                product = Product(
                    id=title_anchor['data-productid'],
                    title=title,
                    url=url,
                    in_stock='product-outofstock' not in ptag['class'],
                    brand=brand
                )

                products.append(product)
            except Exception as e:
                print('Failed to parse product ' + title + ' URL=' + url)
                print(e)

        return products

    def populate_products_variants(self, products: List[Product], products_cache_used: bool):
        log.debug('populating product variants')

        product_ids = [p.id for p in products]
        all_variants_prices = self.sqdc_client.api_calculate_prices(product_ids)

        for product in products:
            product_id = product.id
            variant_prices = [pprice['VariantPrices']
                              for pprice in all_variants_prices
                              if pprice['ProductId'] == product_id][0]
            variants = [
                ProductVariant(
                    id=v['VariantId'],
                    product_id=product_id,
                    list_price=ProductsUpdater.parse_price(v['ListPrice']),
                    price=ProductsUpdater.parse_price(v['DisplayPrice']),
                    price_per_gram=ProductsUpdater.parse_price(v['PricePerGram']),
                    in_stock=False
                )
                for v in variant_prices
            ]
            self.merge_variants(product, variants)

        self.populate_products_variants_details(products, products_cache_used)

        for p in products:
            p.in_stock = p.is_in_stock()

    @staticmethod
    def merge_variants(product, variants_to_merge):
        for v in variants_to_merge:
            resulting_variant = product.get_variant(v.id)
            if not resulting_variant:
                resulting_variant = ProductVariant(id=v.id, product_id=v.product_id)
                product.variants.append(resulting_variant)

            resulting_variant.in_stock = v.in_stock
            resulting_variant.list_price = v.list_price
            resulting_variant.price = v.price
            resulting_variant.price_per_gram = v.price_per_gram

    def _calculate_variant_availability_stats(self, variant: ProductVariant):
        entries = self.store.get_variant_history(variant.product_id, variant.id)
        return ProductHistoryAnalyzer(variant).calculate_percentage_in_stock(variant.product, entries)

    def update_availability_stats(self, product: Product):
        variants = product.get_variants_in_stock()
        if len(variants) == 0:
            return

        eight_variant = next(iter([v for v in variants if v.product_id == product.id and float(v.specifications['GramEquivalent']) == 3.5]), None)
        if eight_variant:
            best_variant = tuple([eight_variant, self._calculate_variant_availability_stats(eight_variant)])
        else:
            best_variant = sorted([tuple([v, self._calculate_variant_availability_stats(v)]) for v in variants], key=lambda x: x[1], reverse=True)[0]

        # log.debug(f'Variant availability: {best_variant[1]}%')
        availability = best_variant[1] if best_variant else None
        product.availability_stats = availability

    @staticmethod
    def parse_price(raw_price: str):
        return float(raw_price.replace('$', ''))

    def populate_products_variants_details(self, products: List[Product], products_cache_used: bool):
        db_products: List[Product]
        if not products_cache_used:
            db_products = self.store.get_products()

        variants_ids_map: Dict[string, ProductVariant] = {}
        for product in filter(lambda p: len(p.variants), products):
            variants_ids_map.update({v.id: v.product_id for v in product.variants})

        variants_ids = list(variants_ids_map.keys())
        variants_in_stock = self.get_variants_ids_in_stock(variants_ids)
        for vid, pid in variants_ids_map.items():
            product = find_by_id(products, pid)
            variant = product.get_variant(vid)
            variant.in_stock = vid in variants_in_stock

            if products_cache_used:
                specs = variant.specifications
            else:
                db_product = find_by_id(db_products, pid)
                db_variant = db_product and db_product.get_variant(vid)
                specs = db_variant and db_variant.specifications
            # Yes.. we never re-fetch specifications (sometimes they change). we should eventually.
            variant.specifications = specs or self.get_variant_specifications(pid, vid)

            product.category = variant.specifications['LevelTwoCategory']
            product.cannabis_type = variant.specifications['CannabisType']
            product.producer_name = variant.specifications['ProducerName']
            variant.quantity_description = SqdcFormatter.format_variant_quantity(variant.specifications['GramEquivalent'])

    def get_variant_specifications(self, product_id, variant_id):
        specifications = self.sqdc_client.api_get_specifications(product_id, variant_id)[0]
        attributes_reformated = {a['PropertyName']: a['Value']
                                 for a in specifications['Attributes']}
        return attributes_reformated

    def get_variants_ids_in_stock(self, variants_ids):
        if self.use_mocked_variants_in_stock:
            ids = ['628582000074', '688083000980', '688083001093', '688083001215', '688083001550', '688083001680', '688083001703', '627560010012',
                    '627560010517', '628582000197', '628582000418', '628582000401', '628582000562', '628582000579', '628582000555', '628582000616',
                    '629108002145', '629108001148', '629108017149', '629108018146', '629108020149', '629108022143', '629108026141', '629108034146',
                    '629108033149', '629108037147', '629108038144', '671148401099', '671148401211', '671148401228', '688083000188', '688083000775',
                    '688083000829', '688083000874', '688083000928', '688083001031', '688083001055', '688083001130', '688083001154', '688083001260',
                    '688083001284', '688083001338', '688083001468', '688083001642', '688083002052', '688083002595', '694144000127', '694144000134',
                    '694144000196', '697238111112', '697238111136', '697238111143', '697238111150', '697238111167', '697238111174', '697238111181',
                    '697238111198', '697238111211', '697238111235', '697238111273', '826966000348', '826966009846', '826966009853', '826966010866',
                    '826966010903', '826966011276', '826966011320', '826966011351', '826966011368', '826966011382', '842865000081', '842865000098',
                    '842865000104', '847023000057', '688083001512', '697238111266', '629108503147', '671148403048', '694144000424', '694144000431',
                    '694144000448', '826966000010', '826966000034', '826966000041', '826966010248', '826966010255', '826966011283', '694144001834',
                    '694144001872', '694144001896', '697238111402', '697238111426', '697238111440', '629108014148', '671148404045', '688083001604',
                    '688083002724', '694144001995', '697238111556', '697238111587', '826966009983', '826966010040', '847023000118']

            num_to_remove = random.randint(0, 5)
            for i in range(num_to_remove):
                ids.remove(ids[i])
            return ids

        else:
            items = self.sqdc_client.api_find_inventory_items(variants_ids)
            log.debug('variants in stock: ')
            # log.debug(items)
            return items
