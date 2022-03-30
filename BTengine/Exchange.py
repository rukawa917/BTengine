class ExchangeRule:
    def __init__(self, maker: float, taker: float, min_val: float):
        self.makerFee = maker
        self.takerFee = taker
        self.min_val = min_val

    def makerFee(self):
        return self.makerFee

    def takerFee(self):
        return self.takerFee

    def min_val(self):
        return self.min_val
