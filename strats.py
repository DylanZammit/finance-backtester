import numpy as np
import pandas as pd
from hist_data import HistData


def cache(f):
    '''
    Checks if this function was previously called.
    In that case, reads cached variable
    '''
    def wrap(self, *args, **kwargs):
        var_name = f'{f.__name__}_'
        if getattr(self, var_name, None) is None:
            setattr(self, var_name, f(self, *args, **kwargs))
        return getattr(self, var_name)
    return wrap


class Strat:

    def __init__(self, prices, capital=1, tc_cost=0, risk=1, risk_scale=True, *args, **kwargs):
        '''
        prices - dataframe of prices
        capital - capital invested.Defaulted to $1
        tc_cost - set transactio cost to $1 by default per trade. Currently allows fractional trades
        risk - in range [0, 1]: annualised risk after transaction costs
        '''
        self.prices = prices
        self.capital = capital
        self.tc_cost = tc_cost
        self.target_risk = risk
        self.args = args
        self.kwargs = kwargs
        self.num_sec = prices.shape[1]
        self.risk_scale = risk_scale

    @property
    @cache
    def signal(self):
        raise NotImplementedError('Each strategy class must have a strategy')

    @property
    @cache
    def tc(self):
        return self.pos_final.diff().abs().mul(self.tc_cost)

    @property
    @cache
    def ret(self):
        return self.prices.apply(np.log).diff()

    @property
    @cache
    def pnl(self):
        return self.pos_final.mul(self.ret).sub(self.tc).sum(axis=1).mul(self.capital)

    @property
    @cache
    def cov(self):
        return self.ret.ewm(252).cov()

    @property
    @cache
    def risk(self):
        if not self.risk_scale:
            return pd.Series(1, index=self.ret.index).apply(np.sqrt)
        # surely there is a neater way similar to
        # return (self.ret.T@cov@self.ret).apply(np.sqrt)
        cov = self.cov.values.reshape(len(self.cov)//self.num_sec, self.num_sec, self.num_sec)
        out = [np.dot(np.dot(cov[i], self.signal.iloc[i]), self.signal.iloc[i]) for i in range(len(cov))]
        return pd.Series(out, index=self.ret.index).apply(np.sqrt)

    @property
    @cache
    def pnl_prerisk(self):
        return self.signal.div(self.risk, axis=0)

    @property
    @cache
    def pos_final(self):
        # div by 16 ~ sqrt(252) to annualise
        AR = 16
        r_com = self.kwargs.get('r_com', 100)
        pnl_tentative = self.pnl_prerisk.mul(self.ret).sum(axis=1)
        risk = pnl_tentative.ewm(r_com).std()
        return self.pnl_prerisk.div(risk, axis=0).mul(self.target_risk).div(AR)

    @property
    @cache
    def pnl_risk(self):
        return self.pos_final.mul(self.ret).sub(self.tc).sum(axis=1)


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


class MeanRevert(Strat):

    @property
    @cache
    def signal(self):
        com = self.kwargs.get('com', 10)
        return -self.ret.ewm(com).mean().shift(1)


if __name__ == '__main__':
    import matplotlib.pyplot as plt
    
    tc_cost = 0.01
    df = pd.read_csv('data.csv', index_col=0)
    lo = LongOnly(df)
    lo_nrc = LongOnly(df, risk_scale=False)
    mo = Momentum(df, com=100)
    mr = MeanRevert(df, com=100)

    lo_tc = LongOnly(df, tc_cost=tc_cost)
    lo_nrc_tc = LongOnly(df, risk_scale=False, tc_cost=tc_cost)
    mo_tc = Momentum(df, com=100, tc_cost=tc_cost)
    mr_tc = MeanRevert(df, com=100, tc_cost=tc_cost)
    
    if 1:
        lo.pnl.cumsum().plot(color='blue')
        lo_nrc.pnl.cumsum().plot(color='pink')
        mo.pnl.cumsum().plot(color='orange')
        mr.pnl.cumsum().plot(color='green')

        alpha = 0.3
        lo_tc.pnl.cumsum().plot(color='blue', alpha=alpha)
        lo_nrc_tc.pnl.cumsum().plot(color='pink', alpha=alpha)
        mo_tc.pnl.cumsum().plot(color='orange', alpha=alpha)
        mr_tc.pnl.cumsum().plot(color='green', alpha=alpha)
        plt.legend(['Long Only', 'Momentum', 'Mean Reversion'])

        plt.show()


    if 0:
        lo.pnl.rolling(10).std().mul(16).plot(color='blue')
        mo.pnl.rolling(10).std().mul(16).plot(color='orange')
        mr.pnl.rolling(10).std().mul(16).plot(color='green')
        plt.legend(['Long Only', 'Momentum', 'Mean Reversion'])

        plt.show()

