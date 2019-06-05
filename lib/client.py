import functools
import time
from typing import List

import requests
from bs4 import BeautifulSoup
import slack
import logging

from lib.product import Product

DEFAULT_LOCALE = 'en-CA'
DOMAIN = 'https://www.sqdc.ca'
BASE_URL = DOMAIN + '/' + DEFAULT_LOCALE

SLACK_API_URL = 'https://slack.com/api'

log = logging.getLogger(__name__)


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
                'User-Agent': 'sqdc-watcher',
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json, text/javascript, */*; q=0.01'
            })

    @staticmethod
    def log_request_elapsed(response: requests.Response):

        log.debug(
            '{} {} completed in {:.2g}s'.format(
                response.request.method,
                response.request.url,
                response.elapsed.total_seconds())
        )

    def _html_get(self, path):
        url = BASE_URL + '/{}'.format(path)
        # print('GET ' + url)
        response = self.session.get(url)
        response.raise_for_status()
        self.log_request_elapsed(response)
        return response.text

    def _api_post(self, path, data, headers={}):
        url = DOMAIN + '/api/{}'.format(path)
        response = self.session.post(url, headers=headers, json=data)
        self.log_request_elapsed(response)
        response.raise_for_status()

        return response.json()

    def post_to_slack(self, post_url, message):
        log.debug('posting to slack')
        payload = {'text': message, "mrkdwn": True, "mrkdwn_in": ["text"]}
        response = self.session.post(post_url, json=payload)
        self.log_request_elapsed(response)
        response.raise_for_status()

    def send_slack_message(self, to_username: str, text: str):
        self.slack_client.chat_postMessage(
            channel='@{}'.format(to_username),
            text=text,
            username='Sqdc Trigger Notifications'
        )

    def get_products(self, max_pages=None) -> List[Product]:
        if max_pages is None:
            max_pages = 999999

        page = 1
        is_finished = False
        products = []
        start_time = time.time()
        while not is_finished and page <= max_pages:
            log.debug('PROCESS results page {}'.format(page))
            products_html = self.get_products_html_page(page)
            products_in_page = self.parse_products_html(products_html)
            is_finished = len(products_in_page) == 0
            if not is_finished:
                page += 1
            products += products_in_page
        self.populate_products_variants(products)

        elapsed = time.time() - start_time
        log.info('COMPLETED - {} products in {} pages scanned in {:.2g}s'.format(len(products), page - 1, elapsed))

        return sorted(
            [Product(p) for p in products],
            key=lambda p: p.get_specification('LevelTwoCategory'))

    def get_products_html_page(self, pagenumber):
        all_products = True
        sort_params = 'SortDirection=asc'
        page_param = 'page={}'.format(pagenumber)
        keywords_param = 'keywords=*'

        if all_products:
            page_path = 'Search?{}&{}&{}'.format(sort_params, keywords_param, page_param)
        else:
            page_path = 'dried-flowers?{}&{}'.format(sort_params, page_param)

        return self._html_get(page_path)

    @staticmethod
    def parse_products_html(raw_html):
        soup = BeautifulSoup(raw_html, 'html.parser')
        product_tags = soup.select('div.product-tile')
        products = []
        for ptag in product_tags:
            title_anchor = ptag.select_one('a[data-qa="search-product-title"]')
            title = title_anchor.contents[0]
            url = DOMAIN + title_anchor['href']
            try:
                brand_tag = ptag.select_one('div[class="js-equalized-brand"]');
                brand = "" if len(brand_tag.contents) == 0 else brand_tag.contents[0]
                product = {
                    'title': title,
                    'id': title_anchor['data-productid'],
                    'url': url,
                    'in_stock': 'product-outofstock' not in ptag['class'],
                    'brand': brand
                }
                products.append(product)
            except Exception as e:
                print('Failed to parse product ' + title + ' URL=' + url)
                print(e)

        return products

    def populate_products_variants(self, products):
        log.debug('populating product variants')

        product_ids = [p['id'] for p in products]
        all_variants_prices = self.api_calculate_prices(product_ids)

        for product in products:
            product_id = product['id']
            variant_prices = [pprice['VariantPrices']
                              for pprice in all_variants_prices
                              if pprice['ProductId'] == product_id][0]
            variants = [
                {
                    'id': v['VariantId'],
                    'product_id': product_id,
                    'list_price': v['ListPrice'],
                    'price': v['DisplayPrice'],
                    'price_per_gram': v['PricePerGram'],
                    'in_stock': False
                } for v in variant_prices
            ]
            product['variants'] = variants

        in_stock_products = [p for p in products if p['in_stock']]
        self.populate_products_variants_details(in_stock_products)

    def populate_products_variants_details(self, products):
        variants_ids_map = {}
        for product in products:
            variants_ids_map.update({v['id']: v['product_id'] for v in product['variants']})
        variants_ids = list(variants_ids_map.keys())
        variants_in_stock = self.api_find_inventory_items(variants_ids)
        for vid, pid in variants_ids_map.items():
            variant_in_stock = vid in variants_in_stock
            if variant_in_stock:
                product = [p for p in products if p['id'] == pid][0]
                variant = [v for v in product['variants'] if v['id'] == vid][0]
                variant['in_stock'] = True
                variant['specifications'] = self.get_variant_specifications(pid, vid)

    def get_variant_specifications(self, product_id, variant_id):
        specifications = self.api_get_specifications(product_id, variant_id)[0]
        attributes_reformated = {a['PropertyName']: a['Value']
                                 for a in specifications['Attributes']}
        return attributes_reformated

    @api_response('ProductPrices')
    def api_calculate_prices(self, product_ids):
        request_payload = {'products': product_ids}
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
