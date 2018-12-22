import logging
from pathlib import Path
import datetime
import json

from lib.product import Product

log = logging.getLogger(__name__)


class SqdcStore:
    def __init__(self, is_test, root_directory=None):
        self.dir = Path(Path.cwd().joinpath('data') if root_directory is None else root_directory)
        if self.dir.is_file():
            raise FileExistsError('The path must be a directory. a file exists here: {}'.format(self.dir))

        if not self.dir.exists():
            self.dir.mkdir()

        test_suffix = '-test' if is_test else ''
        self.products_file = self.dir.joinpath('products{}.json'.format(test_suffix))
        self.config_file = self.dir.joinpath('config.json')
        log.info('INITIALIZED - Using products file: {}'.format(self.products_file))

    def save_products(self, products):
        data_list = [p.data for p in products]
        self.products_file.write_text(json.dumps(data_list))
        print('Saved to ' + self.products_file.absolute().as_posix())

    def get_products(self):
        if not self.products_file.exists():
            return []
        else:
            return [Product(data) for data in json.loads(self.products_file.read_text())]

    def get_products_last_saved_timestamp(self):
        if self.products_file.exists():
            return datetime.datetime.fromtimestamp(self.products_file.stat().st_mtime)
        else:
            return datetime.datetime.min

    def get_config(self):
        if not self.config_file.exists():
            return None
        else:
            return json.loads(self.config_file.read_text())



