import numpy as np
import pandas as pd
from hist_data import HistData
import yaml
import itertools
from IPython import embed


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
        return self.pos_final.mul(self.ret).sub(self.tc).sum(axis=1)

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
        return self.ret.ewm(com).mean().mul(capital).round().shift(1)

#class Momentum(Strat):
#
#    @property
#    @cache
#    def signal(self):
#        com = self.kwargs.get('com', 10)
#        return self.ret.ewm(com).mean().shift(1)

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

def col_gen():
    cols = 'bgrcmykw'
    for col in itertools.cycle(cols):
        yield col

if __name__ == '__main__':
    import matplotlib.pyplot as plt
    
    capital = 1000
    tc_cost = 0.01 # transaction cost as % of trades
    df = pd.read_csv('data.csv', index_col=0)
    df = df[['AAPL', 'ACN', 'ATVI']]

    extras = {'capital': capital}

    # yaml for config
    with open('config.yml', 'r') as f:
        model_params = yaml.safe_load(f)['models']

    models = []
    for name, params in model_params.items():
        model_info = {}
        if params is None: params = {}

        klass = globals()[name]
        model = klass(df, **params, **extras)
        model_tc = klass(df, tc_cost=tc_cost, **params, **extras)

        models.append({'name': name, 'model': model, 'model_tc': model_tc})

    alpha = 0.3
    legends = [m['name'] for m in models]

    c_gen_1 = col_gen()

    for model_info in models:
        name, model, model_tc = model_info.values()
        color = next(c_gen_1)
        model.pnl.cumsum().plot(color=color)
        model_tc.pnl.cumsum().plot(color=color, alpha=alpha)

    plt.legend(legends)

    c_gen_2 = col_gen()
    plt.figure()
    for model_info in models:
        name, model, model_tc = model_info.values()
        color = next(c_gen_2)
        model.pnl.rolling(10).std().mul(16).plot(color=color)

    plt.legend(legends)
    plt.show()

