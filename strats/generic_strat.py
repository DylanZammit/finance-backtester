import pandas as pd
import numpy as np
from utils import cache

class Strat:

    def __init__(
        self, 
        prices, 
        start=None,
        end=None,
        tc_cost=0.02, 
        risk=1, 
        min_trade=0,
        risk_scale=True, 
        *args, **kwargs
    ):
        '''
        prices - dataframe of prices
        capital - capital invested.Defaulted to $1
        tc_cost - set transactio cost to $1 by default per trade. Currently allows fractional trades
        risk - in range [0, 1]: annualised risk after transaction costs
        '''
        if start is None: start = '1900-01-01'
        if end is None: end = '2900-01-01'
        self.prices = prices.loc[start:end]

        self.tc_cost = tc_cost
        self.target_risk = risk

        self.args = args
        self.kwargs = kwargs
        self.num_sec = prices.shape[1]
        self.risk_scale = risk_scale
        self.min_trade = max([0.00001, min_trade])

    @property
    @cache
    def ret(self):
        return self.prices.apply(np.log).diff()

    @property
    @cache
    def cov(self):
        return self.ret.ewm(252).cov()

    @property
    @cache
    def risk(self):
        if not self.risk_scale:
            return pd.Series(1, index=self.ret.index)
        signal = self.signal_smoothed
        # surely there is a neater way similar to
        # return (self.ret.T@cov@self.ret).apply(np.sqrt)
        cov = self.cov.values.reshape(len(self.cov)//self.num_sec, self.num_sec, self.num_sec)
        out = [np.dot(np.dot(cov[i], signal.iloc[i]), signal.iloc[i]) for i in range(len(cov))]
        # techincally has very small vol lookahead at beginning
        return pd.Series(out, index=self.ret.index).apply(np.sqrt).bfill()

    @property
    @cache
    def signal(self):
        raise NotImplementedError('Each strategy class must have a strategy')

    @property
    @cache
    def signal_smoothed(self):
        return self.signal.ewm(5).mean()

    @property
    @cache
    def _pos_basic(self):
        # div by 16 ~ sqrt(252) to annualise
        AR = 16
        r_com = self.kwargs.get('r_com', 100)
        pnl_tentative = self.pnl_prerisk.sum(axis=1)
        risk = pnl_tentative.ewm(r_com).std()
        return self.signal_smoothed.div(self.risk, axis=0).div(risk, axis=0).div(AR)#mul(self.target_risk).div(AR)
        #return self.signal_smoothed.div(self.risk, axis=0).div(risk, axis=0).div(AR).mul(self.target_risk).div(AR)

    @property
    @cache
    def pos(self):
        return self._pos_basic.div(self.min_trade).round().mul(self.min_trade)
        #return self._pos_basic.div(self.min_trade).round().mul(self.min_trade).mul(self.capital)

    @property
    #@cache
    def tc(self):
        return self.pos.diff().abs().mul(self.tc_cost).div(self.prices)

    @property
    @cache
    def pnl_prerisk(self):
        return self.signal_smoothed.mul(self.ret).div(self.risk, axis=0)

    @property
    #@cache
    def pnl(self):
        return self.pos.mul(self.ret).sub(self.tc).sum(axis=1).mul(self.target_risk)

    @property
    #@cache
    def cumpnl(self):
        return self.pnl.cumsum()

    @property
    #@cache
    def drawdown(self):
        return self.cumpnl - self.cumpnl.expanding().max()

    @property
    #@cache
    def sharpe(self):
        return self.pnl.mean()/(self.pnl.std())*16
        #return self.pnl.mean()/(self.pnl.std()*self.capital)*16

