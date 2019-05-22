from lib.slackWatchCommand import SlackWatchCommand
import re


class CommandParser:
    @staticmethod
    def parse(command: str, args: str):
        if command != '/watch':
            raise Exception('Invalid command. we dont handle this one, sorry :s')

        add_match = re.compile('^add (.+)$').match(args)
        delete_match = re.compile('^(delete|del) (.+)$').match(args)
        if args.strip() == "":
            return SlackWatchCommand(verb='list')
        elif add_match:
            print(add_match)
            # keyword
            args_array = [
                add_match.group(1)
            ]
            return SlackWatchCommand(verb='add', args=args_array)
        elif delete_match:
            print(delete_match)
            args_array = [
                delete_match.group(2)
            ]
            return SlackWatchCommand(verb='delete', args=args_array)
        else:
            raise Exception('command not understood')
