#!/usr/bin/env python

import os

import flask
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate

from .data import MotionCtfData


####
#
# Globals
#

# The object holding and monitoring the Relion job output
data = None
from .components import columns_of_interest, overview_figure, motion_figure, ctf_figure, update_figures


####
#
# Layout
#
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
tab_style_fix = {'padding': '6px'}
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
refresh_trigger = dcc.Interval(id='interval-component', interval=25 * 1000, n_intervals=0)
details_table = dash_table.DataTable(id='details_table',
                                     columns=[{"name": i, "id": i} for i in columns_of_interest],
                                     row_selectable='single',
                                     selected_rows=[0],
                                     sort_action='native',
                                     filter_action='native',
                                     fixed_rows={'headers': True, 'data': 0},
                                     style_table={'margin-top': '20px', 'margin-bottom': '20px', 'maxHeight': '40vh',
                                                  'overflowY': 'scroll'})
app.layout = html.Div([
                html.H4(children='mvf: Live Relion Preprocessing'),
                dcc.Tabs([
                    dcc.Tab(label='Overview', style=tab_style_fix, selected_style=tab_style_fix, children=[
                        html.Div([
                            dcc.Graph(id='overview_figure', figure=overview_figure, style={'height': '100vh'}),
                            html.H6(id='mic_counter', children='Total processed micrographs: 0')]),
                        html.Div(style={'border-top': '2px solid #1975FA', 'margin-top': '5vh'}, children=[
                            html.H6('Most recent processed image:')]),
                        html.Div(style={'display': 'flex', 'align-items': 'flex-start'}, children=[
                            html.Img(id='overview_real',
                                     style={'margin': '5px', 'object-fit': 'contain', 'width': '60vw'}),
                            html.Img(id='overview_fft',
                                     style={'margin': '5px', 'object-fit': 'contain', 'width': '40vw'})])]),
                    dcc.Tab(label='Motion', style=tab_style_fix, selected_style=tab_style_fix, children=[
                        dcc.Graph(id='motion_figure', figure=motion_figure, style={'height': '100vh'})]),
                    dcc.Tab(label='CTF', style=tab_style_fix, selected_style=tab_style_fix, children=[
                        dcc.Graph(id='ctf_figure', figure=ctf_figure, style={'height': '120vh'})]),
                    dcc.Tab(label='Details', style=tab_style_fix, selected_style=tab_style_fix, children=[
                        html.Div([details_table]),
                        html.Div([
                            html.H6(children='Selected exposure:'),
                            html.Div(style={'display': 'flex', 'align-items': 'flex-start', 'margin': '20px'},
                                     children=[
                                html.Img(id='details_real',
                                         style={'margin': '5px', 'object-fit': 'contain', 'width': '30vw'}),
                                html.Img(id='details_fft',
                                         style={'margin': '5px', 'object-fit': 'contain', 'width': '20vw'}),
                                html.Img(id='details_avrot',
                                         style={'margin': '5px', 'object-fit': 'contain', 'width': '50vw'})
                            ]),
                        ])
                    ])
                ]),
                refresh_trigger])


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


@app.callback([Output('overview_real', 'src'),
               Output('overview_fft', 'src')],
              [Input('interval-component', 'n_intervals')])
def most_recent_images_updater(n_intervals):
    # Update either because the data changed or this is the first interval fired after load/refresh
    if data and (data.update() or n_intervals == 0) and data.data:
        route_path = 'previews/{}.png'
        overview_real = route_path.format(os.path.split(data.data['rlnMicrographName'][-1])[-1])
        overview_fft = route_path.format(os.path.split(data.data['rlnCtfImage'][-1][:-4])[-1])
        # overview_ctfplot = route_path.format(os.path.split(data.data['rlnCtfImage'][-1][:-8] + '_avrot.txt')[-1])
        return overview_real, overview_fft
    else:
        raise PreventUpdate


@app.callback(Output('details_table', 'data'),
              [Input('interval-component', 'n_intervals')])
def details_table_updater(n_intervals):
    # Update either because the data changed or this is the first interval fired after load/refresh
    if data and (data.update() or n_intervals == 0) and data.data:
        return data.to_datatable_format(columns_of_interest)
    else:
        raise PreventUpdate


@app.callback([Output('details_table', 'style_data_conditional'),
               Output('details_real', 'src'),
               Output('details_fft', 'src'),
               Output('details_avrot', 'src')],
              [Input('details_table', 'selected_rows')])
def row_selected_updater(selected_rows):
    # Note that, unlike plotly, Dash indices do start with 0
    new_selector = [{'if': {'row_index': i}, 'background_color': '#D2F3FF'} for i in selected_rows]
    route_path = 'previews/{}.png'
    details_real = route_path.format(os.path.split(data.data['rlnMicrographName'][selected_rows[0]])[-1])
    details_fft = route_path.format(os.path.split(data.data['rlnCtfImage'][selected_rows[0]][:-4])[-1])
    details_avrot = route_path.format(os.path.split(data.data['rlnCtfImage'][selected_rows[0]][:-8] + '_avrot.txt')[-1])
    return new_selector, details_real, details_fft, details_avrot


@app.server.route('/previews/<image_path>.png')
def serve_image(image_path):
    if data and data.data:
        image_filename = '{}.png'.format(image_path)
        project_img_path = os.path.join(os.path.dirname(data.path), 'Previews')
        return flask.send_from_directory(project_img_path, image_filename)
    else:
        flask.abort(404)


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
    refresh_trigger.interval = 1000 * cfreq


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
