import itertools


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

def col_gen():
    cols = 'bgrcmykw'
    for col in itertools.cycle(cols):
        yield col


def get_SnP_tickers():
    import pandas as pd
    url = r'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    df = pd.read_html(url)[0]
    tickers = ','.join(df.Symbol)
    return tickers

if __name__=='__main__':
    print(get_SnP_tickers())
