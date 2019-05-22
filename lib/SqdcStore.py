import logging
from pathlib import Path
import datetime
import json
import sqlite3

from lib.notificationRule import NotificationRule
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
        self.sqlite_db = self.dir.joinpath('data.db')
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

    def open_connection(self):
        is_new = not Path.exists(self.sqlite_db)
        db = sqlite3.connect(self.sqlite_db.as_posix())

        if is_new:
            db.execute('''CREATE TABLE triggers
                                    (username INT      NOT NULL,
                                    keyword   CHAR[50] NOT NULL,
                                    PRIMARY KEY (username, keyword));
                                    ''')
        return db

    # Returns True if the keyword was added, and False if the keyword was not added because it already exists.
    def add_watch_keyword(self, username, keyword):
        db = self.open_connection()

        cursor = db.execute('SELECT 1 FROM triggers WHERE username = ? AND keyword = ?', (username, keyword))
        if cursor.fetchone():
            return False

        db.execute('INSERT INTO triggers (username, keyword) VALUES (?, ?);', (username, keyword))
        db.commit()
        db.close()
        return True

    def get_user_notification_rules(self, username):
        db = self.open_connection()
        cursor = db.execute('SELECT username, keyword FROM triggers WHERE username = ?', (username,))
        results = []
        for row in cursor:
            username = row[0]
            keyword = row[1]
            results.append(NotificationRule(keyword, username))
        db.close()
        return results

    def get_all_notification_rules(self):
        db = self.open_connection()
        cursor = db.execute('SELECT username, keyword FROM triggers ORDER BY username')
        results = {}
        for row in cursor:
            username = row[0]
            keyword = row[1]

            if username in results:
                user_list = results[username]
            else:
                user_list = results[username] = []
            user_list.append(NotificationRule(keyword, username))
        db.close()
        return results

    def delete_watch_keyword(self, username, keyword):
        db = self.open_connection()
        result = db.execute('DELETE FROM triggers WHERE username = ? AND keyword = ?;', (username, keyword)).rowcount > 0
        db.commit()
        db.close()
        return result
