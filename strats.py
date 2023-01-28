import yaml
import numpy as np
import pandas as pd
from utils import cache, col_gen
from generic_strat import Strat


class LongOnly(Strat):

    @property
    @cache
    def signal(self):
        return self.prices.div(self.prices)


class Momentum(Strat):

    @property
    @cache
    def signal(self):
        com = self.kwargs.get('com', 10)
        return self.ret.ewm(com).mean().shift(1)


class ShortOnLong(Strat):

    @property
    @cache
    def signal(self):
        slow = self.kwargs.get('slow', 50)
        fast = self.kwargs.get('fast', 10)
        slow_ewm = self.ret.ewm(slow).mean()
        fast_ewm = self.ret.ewm(fast).mean()
        return fast_ewm.sub(slow_ewm).mul(capital).shift()


class MeanRevert(Strat):

    @property
    @cache
    def signal(self):
        com = self.kwargs.get('com', 10)
        return -self.ret.ewm(com).mean().shift(1)


class Pairs(Strat):

    @property
    @cache
    def signal(self):
        pass


