import itertools

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
