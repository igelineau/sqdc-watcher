class NotificationRule:
    def __init__(self, keyword: str, username_to_notify: str):
        self.username_to_notify = username_to_notify
        self.keyword = keyword
