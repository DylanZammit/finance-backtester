import yaml
import strats.strats as strats
import matplotlib.pyplot as plt
import argparse
import pandas as pd
from utils import col_gen


def main():
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--tickers', '-t', dest='tickers', help='comma-separated tickers', type=str)
    parser.add_argument('--data', '-d', dest='data', help='comma-separated tickers', type=str)
    parser.add_argument('--n_comp', '-n', dest='n_comp', help='choose via PCA', type=int)
    args = parser.parse_args()

    
    df = pd.read_csv(args.data, index_col=0)

    if args.tickers is not None:
        tickers = args.tickers.split(',')
    elif args.n_comp is not None:
        raise NotImplementedError
        # has lookahead!! Using all data
        # These methods still a WIP
        # tickers = top_uncorr(df, 5)
        # tickers = pick_stocks_PCA(df, 5)
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
        klass = getattr(strats, strat)
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
