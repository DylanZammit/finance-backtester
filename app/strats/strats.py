import yaml
import numpy as np
import pandas as pd
from utils import cache, col_gen
from .generic_strat import Strat


class LongOnly(Strat):
    description = '''
        Buy exactly one unit of risk of each security. No parameters required.
    '''

    @property
    @cache
    def signal(self):
        return self.prices.div(self.prices)


class Momentum(Strat):
    description = '''
        If the returns are greater than the X-day moving average, then buy the stock.
        Otherwise short the stock.
    '''

    @property
    @cache
    def signal(self):
        com = self.kwargs.get('com', 10)
        return self.ret.ewm(com).mean().shift(1)


class ShortOnLong(Strat):
    description = '''
        If the X-day (fast) moving average is above the Y-day (slow) exponentially-weighted moving average (EWMA) then buy the stock. Otherwise short the
        stock.
    '''

    @property
    @cache
    def signal(self):
        slow = self.kwargs.get('slow', 50)
        fast = self.kwargs.get('fast', 10)
        slow_ewm = self.ret.ewm(slow).mean()
        fast_ewm = self.ret.ewm(fast).mean()
        return fast_ewm.sub(slow_ewm).mul(capital).shift()


class MeanRevert(Strat):
    description = '''
        If the returns are lower than the X-day exponentially-weighted moving average (EWMA), then buy the stock.
        Otherwise short the stock.
    '''

    @property
    @cache
    def signal(self):
        com = self.kwargs.get('com', 10)
        return -self.ret.ewm(com).mean().shift(1)

class LongNoVol(Strat):
    description = '''
        Buy exactly one unit of risk of each security. If the X-day rolling volatility exceeds a threshold Y, sell everything.
    '''

    @property
    @cache
    def signal(self):
        com = self.kwargs.get('com', 10)
        thresh = self.kwargs.get('thresh', 0.8)
        bigvol = self.ret.div(self.ret.std()).rolling(com).std().shift(1) < thresh
        return self.prices.div(self.prices).mul(bigvol)


class Pairs(Strat):

    @property
    @cache
    def signal(self):
        pass


