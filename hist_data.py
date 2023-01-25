import yfinance as yf


class HistData:

    def __init__(self, tickers=None):
        '''
        tickers - str or list of tickers
        '''
        if not tickers:
            raise ValueError('Please specify list of tickers or single ticker.')

        if isinstance(tickers, str):
            tickers = [tickers]

        tickers = ' '.join(tickers)

        self.tickers = yf.Tickers(tickers)

    def get_data(self, start, end, interval='1d', **kwargs):
        '''
        start - start date in form %Y-%m-%d
        stop - stop date in form %Y-%m-%d
        '''
        df = self.tickers.download(interval=interval, start=start, end=end, **kwargs)
        df = df['Close'] # I am ignoring more potentially relevant data
        return df



if __name__ == '__main__':
    tickers = ['AAPL', 'MSFT', 'MMM', 'AOS', 'ACN', 'ATVI']
    hd = HistData(tickers)
    df = hd.get_data('2010-01-01', '2023-01-01').to_csv('data.csv')
