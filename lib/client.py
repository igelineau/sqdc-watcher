import functools
import requests
from bs4 import BeautifulSoup
import json

DEFAULT_LOCALE = 'en-CA'
DOMAIN = 'https://www.sqdc.ca'
BASE_URL = DOMAIN + '/' + DEFAULT_LOCALE


def api_response(root_key=''):
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            response_json = fn(*args, **kwargs)
            if not root_key:
                return response_json
            return response_json[root_key]

        return wrapper

    return decorator


class SqdcClient:
    def __init__(self, session=None, locale=DEFAULT_LOCALE):
        self.locale = locale
        if session is None:
            session = requests.Session()
        self.session = session

        self._init_session()

    def _init_session(self):
        self.session.cookies.set('isEighteen', '1')
        self.session.headers.update(
            {
                'Accept-Language': DEFAULT_LOCALE,
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json, text/javascript, */*; q=0.01'
            })

    def _html_get(self, path):
        url = BASE_URL + '/{}'.format(path)
        # print('GET ' + url)
        response = self.session.get(url)
        response.raise_for_status()
        return response.text

    def _api_post(self, path, data, headers={}):
        url = DOMAIN + '/api/{}'.format(path)
        # print('POST' + url)
        response = self.session.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()

    def get_products(self):
        page = 1
        is_finished = False
        products = []
        while not is_finished:
            print('page {}'.format(page))
            products_html = self.get_products_html_page(page)
            products_in_page = self.parse_products_html(products_html)
            is_finished = len(products_in_page) == 0
            if not is_finished:
                page += 1
            products += products_in_page

        print('scan completed ({} pages)'.format(page - 1))
        return products

    def get_products_html_page(self, pagenumber):
        page_path = 'dried-flowers?SortBy=DisplayName&SortDirection=asc'
        if pagenumber > 1:
            page_path += '&page=' + str(pagenumber)
        return self._html_get(page_path)

    def parse_products_html(self, raw_html):
        soup = BeautifulSoup(raw_html, 'html.parser')
        product_tags = soup.select('div.product-tile')
        products = []
        for ptag in product_tags:
            title_anchor = ptag.select_one('a[data-qa="search-product-title"]')

            product = {
                'title': title_anchor.contents[0],
                'id': title_anchor['data-productid'],
                'url': DOMAIN + title_anchor['href'],
                'in_stock': 'product-outofstock' not in ptag['class'],
                'brand': ptag.select_one('div[class="js-equalized-brand"]').contents[0]
            }
            product['variants'] = self.get_product_variants(product['id'], in_stock=product['in_stock'])
            products.append(product)

            if product['in_stock']:
                print('Product in stock: ' + self.format_product(product))
        return products

    def get_product_variants(self, product_id, in_stock):
        variants_raw = self.get_product_variants_prices(product_id)
        variants = list(map(lambda variant_raw: {
            'id': variant_raw['VariantId'],
            'list_price': variant_raw['ListPrice'],
            'price': variant_raw['DisplayPrice'],
            'price_per_gram': variant_raw['PricePerGram'],
            'in_stock': False
        }, variants_raw
                            ))
        if in_stock:
            variants_ids = list(map(lambda v: v['id'], variants))
            variants_in_stock = self.api_find_inventory_items(variants_ids)
            for variant_in_stock_id in variants_in_stock:
                for variant in filter(lambda v: v['id'] == variant_in_stock_id, variants):
                    variant['in_stock'] = True
                    variant['specifications'] = self.get_variant_specifications(product_id, variant['id'])
        return variants

    def get_product_variants_prices(self, product_id):
        prices = self.api_calculate_prices(product_id)
        return prices[0]['VariantPrices']

    def get_variant_specifications(self, product_id, variant_id):
        specifications = self.api_get_specifications(product_id, variant_id)[0]
        attributes_reformated = {a['PropertyName']: dict(Value=a['Value'], Title=a['Title'])
                                 for a in specifications['Attributes']}
        print(attributes_reformated)
        return attributes_reformated

    @api_response('ProductPrices')
    def api_calculate_prices(self, product_id):
        request_payload = {'products': [product_id]}
        return self._api_post('product/calculatePrices', request_payload)

    @api_response()
    def api_find_inventory_items(self, skus_list):
        request_payload = {'skus': skus_list}
        return self._api_post('inventory/findInventoryItems', request_payload)

    @api_response('Groups')
    def api_get_specifications(self, product_id, variant_id):
        payload = {'productId': product_id, 'variantId': variant_id}
        return self._api_post('product/specifications', payload)

    @staticmethod
    def format_product(product):
        return 'Name = {}, URL = {}, in_stock = {}'.format(product['title'], product['url'], product['in_stock'])
