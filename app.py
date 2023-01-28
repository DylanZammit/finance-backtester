# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import dash_bootstrap_components as dbc
from plotly.graph_objs.choroplethmapbox import ColorBar
from dash.dependencies import Input, Output
import plotly.graph_objects as go
from dash import Dash, html, dcc
import plotly.express as px
import pandas as pd
import os
import numpy as np
import dash_daq as daq

BASE_PATH = os.path.dirname(os.path.realpath(__file__))
data_path = os.path.join(BASE_PATH, 'data')
asset_path = os.path.join(BASE_PATH, 'assets')
fn_reset_css = os.path.join(asset_path, 'reset.css')

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME])
app.css.append_css({'external_url': fn_reset_css})
app.server.static_folder = 'static'  # if you run app.py from 'root-dir-name' you don't need to specify.
app.title = 'S&P500 Backtest'



#@app.callback(
#    Output('malta-fig', 'figure'),
#    Input('rent-sale-tabs', 'value'),
#    Input('type-quote-dd', 'value'),
#)
#def update_mapbox(trans, prop_type):
#
#    df_trans = df_fmt[(df_fmt.TransactionType==trans)&(df_fmt.PropertyType==prop_type)]
#
#    lat, lon = 35.917973, 14.409943
#    zmin = df_trans.Price.quantile(0.05)
#    zmax = df_trans.Price.quantile(0.95)
#
#    # burgyl, oranges, hot, YlOrBr
#    colorscale = 'solar'
#    fig = go.Figure(
#        go.Choroplethmapbox(
#            geojson=coords, 
#            locations=df_trans.Town, 
#            z=df_trans.Price, 
#            colorscale=colorscale,
#            zmin=zmin, 
#            zmax=zmax, 
#            marker_line_width=0.1,
#            colorbar=ColorBar(
#                bgcolor=light_bg,
#                borderwidth=0,
#                tickcolor='#ffffff',
#                tickfont={"family": "Open Sans", "color": "#ffffff"},
#            )
#        ),
#    )
#
#    mbs = "mapbox://styles/plotlymapbox/cjvprkf3t1kns1cqjxuxmwixz"
#    fig.update_layout(
#        mapbox_style=mbs, 
#        mapbox_zoom=10.1, 
#        mapbox_accesstoken=token, 
#        mapbox_center = {"lat": lat, "lon": lon},
#        plot_bgcolor=light_bg,
#        paper_bgcolor=light_bg,
#        height=700,
#        margin={'b': 20, 'l': 0, 'r': 120, 't': 20},
#        dragmode=False,
#    )
#    return fig
#
#def load_mapbox():
#    graph = dcc.Graph(
#            id='malta-fig', 
#            config={
#                'displayModeBar': False, 
#                #'scrollZoom': False,
#            }, 
#            #animate=True,
#            style={
#                'width': '70%',
#                'float': 'right',
#            }
#        )
#
#    return graph 

#graph = load_mapbox()
#option_pane = load_option_pane()
#hist = load_histogram()


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

content = html.Div(
            [
                html.Div(
                    [
                        html.Div(className='common-option'),
                        html.Div(className='common-option'),
                        html.Div(className='common-option'),
                    ],
                    id='common-area'
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Div(className='option-box'),
                                        html.Div(className='option-box'),
                                        html.Div(className='option-box'),
                                    ],
                                    id='strat-options-container',
                                ),
                                html.Div(
                                    [
                                        html.Div(className='strat-button'),
                                        html.Div(className='strat-button'),
                                    ],
                                    id='add-new',
                                )
                            ],
                            id='option-area'),
                        html.Div(
                            [
                                html.Div(id='graph')
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
