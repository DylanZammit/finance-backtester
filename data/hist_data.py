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
    import argparse
    parser = argparse.ArgumentParser(description='MCMC setup args.')
    parser.add_argument('--tickers', '-t', help='comma-separated tickers', type=str)
    parser.add_argument('--outname', '-o', help='output file name', type=str)
    parser.add_argument('--start', '-s', help='start day: %Y-%m-%d', type=str, default='2010-01-01')
    parser.add_argument('--end', '-e', help='end day: %Y-%m-%d', type=str, default='2023-01-01')
    args = parser.parse_args()

    tickers = args.tickers.split(',')
    hd = HistData(tickers)
    df = hd.get_data(args.start, args.end, interval='1d')
    df.to_csv(args.outname)
