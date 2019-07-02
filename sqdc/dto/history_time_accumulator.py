from datetime import timedelta


class HistoryTimeAccumulator:
    def __init__(self):
        self.time_in_stock = timedelta()
        self.time_out_of_stock = timedelta()

    def add_time(self, time_amount, add_to_in_stock: bool):
        if add_to_in_stock:
            self.time_in_stock += time_amount
        else:
            self.time_out_of_stock += time_amount
