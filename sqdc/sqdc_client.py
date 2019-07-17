import functools
import logging
from typing import Iterable

import requests

from sqdc import SqdcStore

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
    store: SqdcStore
    session: requests.Session

    def __init__(self, session=None, locale=DEFAULT_LOCALE):
        self.locale = locale
        self._init_session(session)
        self.use_mocked_variants_in_stock = True

    def _init_session(self, session: requests.Session):
        self.session = session or requests.Session()
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

    def get_product_result_page_html(self, page_number):
        sort_params = 'SortDirection=asc'
        page_param = 'page={}'.format(page_number)
        keywords_param = 'keywords=*'
        page_path = 'Search?{}&{}&{}'.format(sort_params, keywords_param, page_param)

        return self._html_get(page_path)

    @api_response('ProductPrices')
    def api_calculate_prices(self, product_ids):
        log.info(f'calling product/calculatePrices with {len(product_ids)} product Ids')
        request_payload = {'products': product_ids}
        return self._api_post('product/calculatePrices', request_payload)

    @api_response()
    def api_find_inventory_items(self, skus: Iterable[str]):
        sku_list = list(skus)
        log.info(f'calling inventory/findInventoryItems with {len(sku_list)} skus')
        request_payload = {'skus': sku_list}
        return self._api_post('inventory/findInventoryItems', request_payload)

    @api_response('Groups')
    def api_get_specifications(self, product_id, variant_id):
        payload = {'productId': product_id, 'variantId': variant_id}
        return self._api_post('product/specifications', payload)
