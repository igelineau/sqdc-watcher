from urllib.parse import parse_qs

import tornado.web

from sqdc.SqdcStore import SqdcStore
from sqdc.commandParser import CommandParser


class SlackRequestHandler(tornado.web.RequestHandler):
    store: SqdcStore

    async def post(self):
        parsed_body = parse_qs(self.request.body)

        print(parsed_body)

        command_arg = self.get_argument(name='command')
        text_arg = self.get_argument(name='text', default='')
        username = self.get_argument('user_name')
        print('command = ' + command_arg)
        command = CommandParser.parse(command_arg, text_arg)
        if command.verb == "list":
            print('username => ' + username)
            rules = self.store.get_user_notification_rules(username)
            nb_rules = len(rules)
            if nb_rules == 0:
                response = 'You do not have any keyword trigger registered yet.'
            else:
                keyword_word = 'keyword' if nb_rules == 1 else 'keywords'
                response = 'You have *{} registered {}:*\n'.format(nb_rules, keyword_word)
                for rule in rules:
                    response += '- ' + rule.keyword + '\n'
            self.write(response)

        elif command.verb == 'add':
            keyword = command.args[0]
            was_added = self.store.add_watch_keyword(username, keyword)
            if was_added:
                self.write('*{}* keyword added. You will receive a notification whenever a match is found in new products.'
                           .format(keyword))
            else:
                self.write('Keyword *{}* is already registered.'.format(keyword))

        elif command.verb == 'delete':
            keyword = command.args[0]
            was_deleted = self.store.delete_trigger(username, keyword)
            if was_deleted:
                self.write('Keyword *{}* was removed.'.format(keyword))
            else:
                self.write('Could not delete *{}* because it was not registered.'.format(keyword))
