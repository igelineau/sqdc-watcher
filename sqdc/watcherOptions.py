from typing import List

from sqdc.notificationRule import NotificationRule


class WatcherOptions:
    interval: int
    slack_post_url: str
    slack_token: str
    is_test_mode: bool
    notification_rules: List[NotificationRule]
    display_format: str
    slack_port: int

    def __init__(self):
        self.notification_rules = []

    @staticmethod
    def default():
        options = WatcherOptions()
        options.interval = 60 * 5
        return options
