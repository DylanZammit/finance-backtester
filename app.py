# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import dash_bootstrap_components as dbc
from plotly.graph_objs.choroplethmapbox import ColorBar
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
from dash import Dash, html, dcc, ctx
import plotly.express as px
import pandas as pd
import os
import numpy as np
import dash_daq as daq
from strats.strats import *

BASE_PATH = os.path.dirname(os.path.realpath(__file__))
data_path = os.path.join(BASE_PATH, 'data')
asset_path = os.path.join(BASE_PATH, 'assets')
fn_reset_css = os.path.join(asset_path, 'reset.css')

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME])
app.css.append_css({'external_url': fn_reset_css})
app.server.static_folder = 'static'  # if you run app.py from 'root-dir-name' you don't need to specify.
app.title = 'S&P500 Backtest'
df = pd.read_csv(os.path.join(data_path, 'SNP500.csv'), index_col=0)


applied_strats = {}


@app.callback(
                  Output('strat-pnl', 'figure'),
                  Output('strat-pnl-diff', 'figure'),
              
              [
                  Input('strat-apply', 'n_clicks'),
                  State('option-name', 'value'),
                  State('option-strat', 'value'),
                  State('option-stocks', 'value'),
                  State('option-param1', 'value'),
              ])
def update_pnl_figure(btn_apply, name, strat, stocks, param):
    if strat is None: strat = 'LongOnly'
    if stocks is None: stocks = ['AAPL']
    if name is None: 
        name = 'default'
    else:
        if 'default' in applied_strats:
            del applied_strats['default']
    if len(stocks) > 10: stocks = stocks[:10]

    strat = globals()[strat](df[stocks]) # pass params as well!!
    applied_strats[name] = strat
    

    pnls = []
    pnls_diff = []
    for name, strat in applied_strats.items():
        pnl_strat = strat.pnl
        pnl_strat.name = name

        pnls_diff.append(pnl_strat)
        pnls.append(pnl_strat.cumsum())

    pnls = pd.concat(pnls, axis=1)
    pnls_diff = pd.concat(pnls_diff, axis=1)

    fig = px.line(pnls, x=pnls.index, y=pnls.columns)
    fig_diff = px.line(pnls_diff, x=pnls.index, y=pnls.columns)

    largs = dict(
          colorway=["#5E0DAC", '#FF4F00', '#375CB1', '#FF7400', '#FFF400', '#FF0056'],
          template='plotly_dark',
          paper_bgcolor='rgba(0, 0, 0, 0)',
          plot_bgcolor='rgba(0, 0, 0, 0)',
          margin={'b': 15},
          hovermode='x',
          autosize=True,
          title={'text': 'Stock Prices', 'font': {'color': 'white'}, 'x': 0.5},
    )

    fig.update_layout(**largs)
    fig_diff.update_layout(**largs)

    return fig, fig_diff


PLOTLY_LOGO = "https://images.plot.ly/logo/new-branding/plotly-logomark.png"
sidebar = html.Div(
    [
        html.Div(
            [
                # width: 3rem ensures the logo is the exact width of the
                # collapsed sidebar (accounting for padding)
                html.Img(src=PLOTLY_LOGO, style={"width": "3rem"}),
                html.H2("Sidebar"),
            ],
            className="sidebar-header",
        ),
        html.Hr(),
        dbc.Nav(
            [
                dbc.NavLink(
                    [html.I(className="fas fa-home me-2"), html.Span("Home")],
                    href="/",
                    active="exact",
                ),
                dbc.NavLink(
                    [
                        html.I(className="fas fa-calendar-alt me-2"),
                        html.Span("Calendar"),
                    ],
                    href="/calendar",
                    active="exact",
                ),
                dbc.NavLink(
                    [
                        html.I(className="fas fa-envelope-open-text me-2"),
                        html.Span("Messages"),
                    ],
                    href="/messages",
                    active="exact",
                ),
            ],
            vertical=True,
            pills=True,
        ),
    ],
    className="sidebar",
)

common_area = html.Div(
                    [
                        dcc.Input(
                            type='number', 
                            placeholder='\t€ Capital', 
                            className='common-option',
                            step=1,
                            min=1,
                            id='common-capital',
                        ),
                        dcc.Input(
                            type='number', 
                            placeholder='\t% Transaction Cost', 
                            className='common-option',
                            id='common-tc',
                            min=0,
                            max=5,
                            step=0.5,
                        ),
                        dcc.Input(
                            type='number', 
                            placeholder='\t% Annualized Risk', 
                            className='common-option',
                            id='common-risk',
                            min=0,
                            max=100,
                            step=1,
                        ),
                        html.Div(id='common-update-button'),
                    ],
                    id='common-area'
                )

option_area = html.Div(
                [
                    html.Div(
                        [
                            dcc.Input(
                                type='text', 
                                placeholder='\tSet Strategy Name', 
                                className='option-box',
                                id='option-name',
                            ),
                            dcc.Dropdown(
                                {
                                    'LongOnly': 'Long Only',
                                    'Momentum': 'Momentum', 
                                    'MeanRevert': 'Mean Reverting'
                                },
                                placeholder='\tChoose Strategy', 
                                className='option-box',
                                id='option-strat',
                            ),
                            dcc.Dropdown(
                                df.columns.sort_values(),
                                ['AAPL'],
                                placeholder='\tPick Stocks', 
                                className='option-box',
                                id='option-stocks',
                                multi=True,
                            ),
                            dcc.Input(
                                type='number',
                                placeholder='\tEWMA CoM (days)', 
                                className='option-box',
                                id='option-param1',
                            ),
                        ],
                        id='strat-options-container',
                    ),
                    html.Div(
                        [
                            html.Div(className='strat-button', id='strat-apply'),
                            html.Div(className='strat-button', id='strat-cancel'),
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
                        html.Div(
                            [
                                dcc.Graph(id='strat-pnl', config={'displayModeBar': False}),
                                dcc.Graph(id='strat-pnl-diff', config={'displayModeBar': False}),
                            ],
                            id='graph-area')
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
    app.run_server(debug=True)
