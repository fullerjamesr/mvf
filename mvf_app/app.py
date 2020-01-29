#!/usr/bin/env python

import os

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate

from .data import MotionCtfData
from .components import overview_figure, motion_figure, ctf_figure, update_figures


####
#
# Layout
#
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
tab_style_fix = {'padding': '6px'}
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.layout = html.Div([
                html.H3(children='MVF: Live Relion Preprocessing'),
                dcc.Tabs([
                    dcc.Tab(label='Overview', style=tab_style_fix, selected_style=tab_style_fix, children=[
                        html.Div([
                            dcc.Graph(id='overview_figure', figure=overview_figure, style={'height': '100vh'}),
                            html.H6(id='mic_counter', children='Total processed micrographs: 0')])]),
                    dcc.Tab(label='Motion', style=tab_style_fix, selected_style=tab_style_fix, children=[
                        dcc.Graph(id='motion_figure', figure=motion_figure, style={'height': '100vh'})]),
                    dcc.Tab(label='CTF', style=tab_style_fix, selected_style=tab_style_fix, children=[
                        dcc.Graph(id='ctf_figure', figure=ctf_figure, style={'height': '120vh'})])]),
                dcc.Interval(id='interval-component', interval=25 * 1000, n_intervals=0)])


data = None


####
#
# Callbacks
#
@app.callback([Output('mic_counter', 'children'),
               Output('overview_figure', 'figure'),
               Output('motion_figure', 'figure'),
               Output('ctf_figure', 'figure')],
              [Input('interval-component', 'n_intervals')])
def motion_ctf_progress_updater(n_intervals):
    # Update either because the data changed or this is the first interval fired after load/refresh
    if data and (data.update() or n_intervals == 0) and data.data:
        new_count = len(data.data[next(iter(data.data))])
        new_count_str = "Total processed micrographs: {}".format(new_count)
        update_figures(data.data)
        return new_count_str, overview_figure, motion_figure, ctf_figure
    else:
        raise PreventUpdate


####
#
# Main
#

# ! WSGI entry point !
server = app.server

def main(opts=os.environ):
    global app, data
    project_dir = opts.get('MVF_PROJECT_DIR', os.getcwd())
    cfreq = int(opts.get('MVF_CFREQ', 10))
    hint_file_path = os.path.join(os.path.abspath(project_dir), '.mvf_progress_hint')
    data = MotionCtfData(hint_file_path)
    app.layout.children[-1].interval = 1000 * cfreq


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="Launch an instance of the MVF Dash Server",
                                     epilog="https://github.com/fullerjamesr/mvf")
    parser.add_argument("--cfreq", default=10, type=int,
                        help="Frequency in seconds to direct clients to poll server (default: 10")
    parser.add_argument("project_dir", nargs='?',
                        help="The Relion/MVF project directory to be served", default=os.getcwd())
    args = parser.parse_args()
    cli_opts = {'MVF_PROJECT_DIR': args.project_dir, 'MVF_CFREQ': args.cfreq}
    main(cli_opts)
    app.run_server(debug=True)
else:
    main()
