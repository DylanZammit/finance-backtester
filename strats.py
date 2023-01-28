import numpy as np
import pandas as pd
from hist_data import HistData
import yaml
from utils import cache, col_gen
from IPython import embed


class Strat:

    def __init__(
        self, 
        prices, 
        start=None,
        end=None,
        capital=1, 
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
        self.capital = capital
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
        return self.signal_smoothed.div(self.risk, axis=0).div(risk, axis=0).mul(self.target_risk).div(AR)

    @property
    @cache
    def pos(self):
        return self._pos_basic.div(self.min_trade).round().mul(self.min_trade).mul(self.capital)

    @property
    @cache
    def tc(self):
        return self.pos.diff().abs().mul(self.tc_cost).div(self.prices)

    @property
    @cache
    def pnl_prerisk(self):
        return self.signal_smoothed.mul(self.ret).div(self.risk, axis=0)

    @property
    @cache
    def pnl(self):
        return self.pos.mul(self.ret).sub(self.tc).sum(axis=1)

    @property
    @cache
    def sharpe(self):
        return self.pnl.iloc[-1]/(self.pnl.std()*self.capital)


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

####################################################

def pick_stocks_PCA(df, n):
    '''
    WORK IN PROGRESS
    '''
    df = df.dropna(axis=1, how='any')
    df_ret = df.apply(np.log).diff().dropna()
    df_scaled = df_ret.sub(df_ret.mean()).div(df_ret.std())
    cov = df_scaled.cov()
    eig_val, eig_vec = np.linalg.eig(cov)

    idx = np.argsort(eig_val)[::-1]

    tot_var = sum(eig_val)
    pct_explained = sum(eig_val[idx][:n])/tot_var
    chosen = df.columns[idx][:n]
    print(f'Chosen stocks = {chosen}')
    print(f'% Explained = {pct_explained}')

    feat = eig_vec[idx][:,:n]
    X = feat.T@df_scaled.T

    return chosen

def top_uncorr(df, n):
    '''
    Improve this method
    '''
    df = df.dropna(axis=1, how='any')
    df_ret = df.apply(np.log).diff().dropna()
    #df_scaled = df_ret.sub(df_ret.mean()).div(df_ret.std())
    df_scaled = df_ret
    corr_table = df_scaled.corr()
    corr_table['stock1'] = corr_table.index
    corr_table = corr_table.melt(id_vars = 'stock1', var_name = "stock2").reset_index(drop = True)
    corr_table = corr_table[corr_table['stock1'] < corr_table['stock2']].dropna()
    corr_table['abs_value'] = np.abs(corr_table['value'])
    highest_corr = corr_table.sort_values("abs_value",ascending = True).head(20)
    chosen = np.unique(highest_corr.iloc[:5][['stock1', 'stock2']].values)
    return chosen

def main():
    import matplotlib.pyplot as plt
    import argparse
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--tickers', '-t', dest='tickers', help='comma-separated tickers', type=str)
    parser.add_argument('--data', '-d', dest='data', help='comma-separated tickers', type=str)
    parser.add_argument('--n_comp', '-n', dest='n_comp', help='choose via PCA', type=int)
    args = parser.parse_args()

    
    df = pd.read_csv(args.data, index_col=0)

    if args.tickers is not None:
        tickers = args.tickers.split(',')
    elif args.n_comp is not None:
        # has lookahead!! Using all data
        # These methods still a WIP
        tickers = top_uncorr(df, 5)
        #tickers = pick_stocks_PCA(df, 5)
    else:
        tickers = df.columns

    df = df[tickers]

    # yaml for config
    with open('config.yml', 'r') as f:
        params = yaml.safe_load(f)

    common = params['common']
    common_no_tc = common.copy()
    common_no_tc['tc_cost'] = 0
    model_params = params['models']

    models = []
    legends = []
    for name, params in model_params.items():
        if params is None: params = {}

        strat = params.pop('strat')
        klass = globals()[strat]
        model = klass(df, **common_no_tc, **params)
        model_tc = klass(df, **common, **params)

        models.append({'name': name, 'model': model, 'model_tc': model_tc})
        legends.append(name)
        legends.append('_nolegend_')

    c_gen_1 = col_gen()

    # pnl plot
    for model_info in models:
        color = next(c_gen_1)

        name, model, model_tc = model_info.values()
        model.pnl.iloc[100:].cumsum().plot(color=color)
        model_tc.pnl.iloc[100:].cumsum().plot(color=color, alpha=0.4)

    plt.axhline(y=0, color='black')
    plt.legend(legends)

    c_gen_2 = col_gen()
    plt.figure()

    # risk plot
    for model_info in models:
        color = next(c_gen_2)

        name, model, model_tc = model_info.values()
        model.pnl.iloc[100:].rolling(50).std().mul(16).div(model.capital).plot(color=color)
        print('{} volatility = {:.2f}'.format(name, model.pnl.std()))
        print('{} sharpe = {:.2f}'.format(name, model.sharpe))

    legends = [legends[i] for i in range(0, len(legends), 2)]
    plt.legend(legends)

    # pos plot
    fig, ax = plt.subplots(len(models))
    for i, model in enumerate(models):
        model['model'].pos.iloc[100:].plot(ax=ax[i])
        ax[i].set_title('{} position'.format(model['name']))

    plt.show()


if __name__ == '__main__':
    main()
