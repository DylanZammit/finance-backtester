# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import dash_bootstrap_components as dbc
from plotly.graph_objs.choroplethmapbox import ColorBar
from dash.dependencies import Input, Output, State, ALL
import plotly.graph_objects as go
from dash import Dash, html, dcc, ctx
import plotly.express as px
import pandas as pd
import os
import numpy as np
import dash_daq as daq
from strats.strats import *
import json

with open('sec.json', 'r') as f:
    tick_sec = json.loads(f.read())
tick_sec = {k: f'{k} - {v}' for k, v in tick_sec.items()}
tick_sec = dict(sorted(tick_sec.items(), key=lambda item: item[1]))

BASE_PATH = os.path.dirname(os.path.realpath(__file__))
data_path = os.path.join(BASE_PATH, 'data')
asset_path = os.path.join(BASE_PATH, 'assets')
fn_reset_css = os.path.join(asset_path, 'reset.css')

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME])
app.css.append_css({'external_url': fn_reset_css})
app.server.static_folder = 'static'  # if you run app.py from 'root-dir-name' you don't need to specify.
app.title = 'S&P500 Backtest'
server = app.server
df = pd.read_csv(os.path.join(data_path, 'SNP500.csv'), index_col=0)

LINKEDIN_ICO = 'fas fa-brands fa-linkedin'
SQUARE_MINUS_ICO = 'fas fa-regular fa-square-minus'


@app.callback(
      Output('strat-pnl', 'figure'),
      Output('strat-pnl-diff', 'figure'),
      Output('summary-container', 'children'),

      Output('option-name', 'value'),
      Output('option-strat', 'value'),
      Output('option-stocks', 'value'),
      Output('strat-params-container', 'children'),
  [
      Input('strat-apply', 'n_clicks'), # 1
      Input('strat-cancel', 'n_clicks'), # 2
      State('option-name', 'value'), # 3
      State('option-strat', 'value'), # 4
      State('option-stocks', 'value'), # 5
      State({'type': 'strat-param-option', 'index': ALL, 'param': ALL}, 'id'), # 6
      State({'type': 'strat-param-option', 'index': ALL, 'param': ALL}, 'value'), # 7
      State('summary-container', 'children'), # 8
      Input({'type': 'summary-remove', 'index': ALL}, 'n_clicks'), # 9
      State({'type': 'summary-remove', 'index': ALL}, 'id'), # 10

      Input('common-update-button', 'n_clicks'), # 11
      State('common-risk', 'value'), # 12
      State('common-tc', 'value'), # 13
      State('fig-maj-dd', 'value'), # 14
      State('fig-min-dd', 'value'), # 15

      Input('option-strat', 'value'), #16
  ]
)
def update_pnl_figure(
    btn_apply, # 1
    btn_cancel, # 2
    input_name, # 3
    strat, # 4
    stocks, # 5
    param_id, # 6
    param_val, # 7
    container, # 8
    n_click, # 9
    btn_remove, #10
    n, # 11
    risk, # 12
    tc, # 13
    minfig, # 14
    majfig, # 15
    strat_val # 16
):
    strat_param_map = {
        'LongOnly': {},
        'Momentum': {'EWMA Window': 'com'},
        'MeanRevert': {'EWMA Window': 'com'},
    }
    if isinstance(ctx.triggered, list) and ctx.triggered[0]['prop_id'] == 'option-strat.value':
        strat_params_container = [
            dcc.Input(
                type='number',
                placeholder=k, 
                className='option-box',
                id={'type': 'strat-param-option', 'index': strat_val, 'param': v}
            )
            for k, v in strat_param_map[strat_val].items()
        ]

        fig, fig_diff = get_fig('PnL', 'Risk')
        return fig, fig_diff, container, input_name, strat, stocks, strat_params_container
    elif ctx.triggered_id == 'strat-apply':
        if strat is None: strat = 'LongOnly'
        if stocks is None: stocks = []
        #if stocks is None: stocks = ['AAPL']
        if len(stocks) > 10: stocks = stocks[:10]

        kwargs = {pid['param']: pval for pid, pval in zip(param_id, param_val)}
        new_strat = globals()[strat](df[stocks], **kwargs)
        applied_strats[input_name] = new_strat
    
        summary = html.Div(
            [
                html.Div(input_name[:2], className='summary-short-name'),
                html.Div(input_name, className='summary-name'),
                html.Div(f'{new_strat.sharpe:.2f}', className='summary-sharpe'),
                html.I(className=f'{SQUARE_MINUS_ICO} summary-remove', id={'type': 'summary-remove', 'index': input_name}),
            ],
            className='summary-strat', id=f'{input_name}_strat'),

        container.append(summary[0])
        fig, fig_diff = get_fig('PnL', 'Risk')
        return fig, fig_diff, container, '', None, [], []
    elif ctx.triggered_id == 'strat-cancel':
        fig, fig_diff = get_fig('PnL', 'Risk')
        return fig, fig_diff, container, '', None, [], []
    elif isinstance(ctx.triggered_id, dict) and ctx.triggered_id['type'] == 'summary-remove':
        removed_strat = ctx.triggered_id['index']
        del applied_strats[removed_strat]
        
        container = [c for c in container if c['props'].get('id', '') != f'{removed_strat}_strat']
        fig, fig_diff = get_fig('PnL', 'Risk')
        return fig, fig_diff, container, '', None, [], []
    elif ctx.triggered_id == 'common-update-button':

        for k, v in applied_strats.items():
            v.target_risk = int(risk)/100
            v.tc_cost = int(tc)/100

        fig, fig_diff = get_fig(minfig, majfig)

        return fig, fig_diff, container, '', None, [], []

    else:
        for input_name, new_strat in applied_strats.items():
            summary = html.Div(
                [
                    html.Div(input_name[:2], className='summary-short-name'),
                    html.Div(input_name, className='summary-name'),
                    html.Div(f'{new_strat.sharpe:.2f}', className='summary-sharpe'),
                    html.I(className=f'{SQUARE_MINUS_ICO} summary-remove', id={'type': 'summary-remove', 'index': input_name}),
                ],
                className='summary-strat', id=f'{input_name}_strat'),

            container.append(summary[0])

        fig, fig_diff = get_fig('PnL', 'Risk')
        return fig, fig_diff, container, '', None, [], []


def get_fig(*args):

    figs = []
    for figtype in args:

        data = pd.DataFrame()

        for name, strat in applied_strats.items():
            my_figtype = figtype
            if figtype.lower() == 'pnl':
                my_figtype = 'cumpnl'
            if my_figtype.lower() == 'risk':
                pdata = getattr(strat, 'pnl').rolling(50, min_periods=1).std()*16
            else:
                pdata = getattr(strat, my_figtype.lower())

            pdata.name = name
            data = pd.concat([data, pdata], axis=1)


        #if not len(minfig_data):
        #    pnls = pd.DataFrame(index=df.index)
        #    pnls_diff = pd.DataFrame(index=df.index)

        fig = px.line(data, x=data.index, y=data.columns)

        largs = dict(
            colorway=["#5E0DAC", '#FF4F00', '#375CB1', '#FF7400', '#FFF400', '#FF0056'],
            template='plotly_dark',
            paper_bgcolor='rgba(0, 0, 0, 0)',
            plot_bgcolor='rgba(0, 0, 0, 0)',
            margin={'b': 15},
            #margin=dict(l=25, r=25, t=55, b=5),
            hovermode='x',
            autosize=True,
            title={'text': figtype, 'font': {'color': 'white'}, 'x': 0.5},
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
            legend_title_text=None,
            yaxis_title=None,
            xaxis_title=None,
        )

        fig.update_layout(**largs)
        figs.append(fig)

    return tuple(figs)

PLOTLY_LOGO = "https://images.plot.ly/logo/new-branding/plotly-logomark.png"
PLOTLY_LOGO = 'https://thumbs.dreamstime.com/b/logo-candlestick-trading-chart-analyzing-forex-stock-market-92714359.jpg'
sidebar = html.Div(
    [
        html.Div(
            [
                # width: 3rem ensures the logo is the exact width of the
                # collapsed sidebar (accounting for padding)
                html.Img(src=PLOTLY_LOGO, style={"width": "3rem"}),
                html.H2("Strategies"),
            ],
            className="sidebar-header",
        ),
        html.Hr(),
        html.Div(
            [
                html.Div(
                    [
                        html.Div(className='summary-short-name'),
                        html.Div('Name', className='summary-name'),
                        html.Div('Sharpe', className='summary-sharpe'),
                        html.Div('Del', className='summary-del'),
                    ],
                    className='summary-strat', id='summary-strat-title'),
                    html.Hr(className='summary-hline'),
            ],
            id='summary-container'
        ),
        html.Div(
            [
                html.A(html.I(className=f'{LINKEDIN_ICO} linkedin', id='linkedin-logo'), href='https://www.linkedin.com/in/dylanzam/', target='_blank'),
                html.A(html.H2('Dylan Zammit'), href='https://www.linkedin.com/in/dylanzam/', target='_blank',
                       id='linkedin-text'),
            ],
            id='linkedin-container'
        ),
    ],
    className="sidebar",
)
#from dash.dash_table.Format import Format, Scheme, Sign, Symbol
common_area = html.Div(
                    [
                        dcc.Dropdown(
                            {i: f'{i}% Transaction Cost' for i in range(0, 6)},
                            value='0',
                            id='common-tc',
                            clearable=False,
                            searchable=False,
                        ),
                        dcc.Dropdown(
                            {i: f'{i}% Annualized Risk' for i in range(5, 105, 5)},
                            value='100',
                            #placeholder='% Annualized Risk', 
                            id='common-risk',
                            clearable=False,
                            searchable=False,
                        ),
                        dcc.Dropdown(
                            ['PnL', 'Risk', 'Drawdown'],
                            'PnL',
                            placeholder='Major Plot', 
                            id='fig-maj-dd',
                            clearable=False,
                            searchable=False,
                        ),
                        dcc.Dropdown(
                            ['PnL', 'Risk', 'Drawdown'],
                            'Risk',
                            placeholder='Minor Plot', 
                            id='fig-min-dd',
                            clearable=False,
                            searchable=False,
                        ),
                        html.Div('Update', id='common-update-button'),
                        #html.H1('Backtester', id='title')
                    ],
                    id='common-area'
                )

option_area = html.Div(
                [
                    html.Div(
                        [
                            html.H2('Portfolio Setup', id='strat-setup-title'),
                            dcc.Input(
                                type='text', 
                                placeholder='Set Strategy Name', 
                                className='option-box',
                                id='option-name',
                            ),
                            dcc.Dropdown(
                                {
                                    'LongOnly': 'Long Only',
                                    'Momentum': 'Momentum', 
                                    'MeanRevert': 'Mean Reverting'
                                },
                                placeholder='Choose Strategy', 
                                className='option-box',
                                id='option-strat',
                                searchable=False,
                            ),
                            dcc.Dropdown(
                                #df.columns.sort_values(),
                                tick_sec,
                                placeholder='Pick Stocks', 
                                className='option-box',
                                id='option-stocks',
                                multi=True,
                            ),
                            html.Hr(className='strat-hline'),
                            html.Div(
                                id='strat-params-container',
                            )
                        ],
                        id='strat-options-container',
                    ),
                    html.Div(
                        [
                            html.Div('Add Strategy', className='strat-button', id='strat-apply'),
                            html.Div('Clear', className='strat-button', id='strat-cancel'),
                        ],
                        id='add-new',
                    )
                ],
                id='option-area')

content = html.Div(
            [
                common_area,
                html.Div(
                    [
                        option_area,
                        dcc.Loading( # have to do style here for some reason
                            [
                                dcc.Graph(id='strat-pnl', config={'displayModeBar': False}),
                                dcc.Graph(id='strat-pnl-diff', config={'displayModeBar': False}),
                            ],
                            id='graph-area',
                            parent_style={
                                'background-color': 'var(--light)',
                                'display': 'flex',
                                'flex-direction': 'column',
                                'flex': 2,
                                'margin': '2%',
                                'height': 'max(auto, 600px)',
                                'outline': 'auto',
                            }
                        ),
                    ],
                    id='model-settings'
                ),
            ],
            id='page-content'
        )

app.layout = html.Div(
    [
        dcc.Location(id="url"),
        sidebar,
        content
    ],
    id='backest'
)

if __name__ == '__main__':
    applied_strats = {}
    MAANG = ['META', 'AMZN', 'AAPL', 'NFLX', 'GOOG']
    long_only_maang = LongOnly(df[MAANG])
    momentum_maang = Momentum(df[MAANG])
    applied_strats['Long MAANG'] = long_only_maang
    applied_strats['Momentum MAANG'] = momentum_maang
    app.run_server(host='0.0.0.0', debug=True)
