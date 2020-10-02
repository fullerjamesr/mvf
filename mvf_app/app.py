#!/usr/bin/env python

import os

import flask
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
from dash.dependencies import Input, Output, State
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
                            html.H6(id='mic_counter', children='Total processed micrographs: 0')
                        ]),
                        html.Div(style={'border-top': '2px solid #1975FA', 'margin-top': '5vh'}, children=[
                            html.H6('Most recent processed image:')
                        ]),
                        html.Div(className='imagerow-container', children=[
                            html.Img(id='overview_real', className='imagerow-member', style={'width': '60vw'}),
                            html.Img(id='overview_fft', className='imagerow-member', style={'width': '40vw'})
                        ]),
                        html.Div(id='overview_modal', className='modal-container', children=[
                            html.Img(id='overview_modal_img', className='modal-content')
                        ])
                    ]),
                    dcc.Tab(label='Motion', style=tab_style_fix, selected_style=tab_style_fix, children=[
                        dcc.Graph(id='motion_figure', figure=motion_figure, style={'height': '100vh'})]),
                    dcc.Tab(label='CTF', style=tab_style_fix, selected_style=tab_style_fix, children=[
                        dcc.Graph(id='ctf_figure', figure=ctf_figure, style={'height': '120vh'})]),
                    dcc.Tab(label='Details', style=tab_style_fix, selected_style=tab_style_fix, children=[
                        html.Div([details_table]),
                        html.Div([
                            html.H6(children='Selected exposure:'),
                            html.Div(className='imagerow-container', style={'margin': '20px'}, children=[
                                html.Img(id='details_real', className='imagerow-member', style={'width': '30vw'}),
                                html.Img(id='details_fft', className='imagerow-member', style={'width': '20vw'}),
                                html.Img(id='details_avrot', className='imagerow-member', style={'width': '50vw'})
                            ]),
                            html.Div(id='details_modal', className='modal-container', children=[
                                html.Img(id='details_modal_img', className='modal-content')
                            ])
                        ])
                    ])
                ]),
                refresh_trigger])


####
#
# Image handling
#
def generate_preview_image_src(filename):
    route_path = 'previews/{}.png'
    return route_path.format(filename)


def generate_mic_image_src(idx):
    global data
    return generate_preview_image_src(os.path.split(data.data['rlnMicrographName'][idx])[-1])


def generate_fft_image_src(idx):
    global data
    return generate_preview_image_src(os.path.split(data.data['rlnCtfImage'][idx][:-4])[-1])


def generate_avrot_image_src(idx):
    global data
    return generate_preview_image_src(os.path.split(data.data['rlnCtfImage'][idx][:-8] + '_avrot.txt')[-1])


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
# Callbacks
#
@app.callback([Output('mic_counter', 'children'),
               Output('overview_figure', 'figure'),
               Output('motion_figure', 'figure'),
               Output('ctf_figure', 'figure'),
               Output('overview_real', 'src'),
               Output('overview_fft', 'src'),
               Output('details_table', 'data')],
              [Input('interval-component', 'n_intervals')])
def progress_updater(n_intervals):
    global data
    # Update either because the data changed or this is the first interval fired after load/refresh
    if data and (data.update() or n_intervals == 0) and data.data:
        # Micrograph counter
        new_count = len(data.data[next(iter(data.data))])
        new_count_str = "Total processed micrographs: {}".format(new_count)

        # Update all graphs
        update_figures(data.data)

        # Update Overview tab most recent images
        overview_micrograph_src = generate_mic_image_src(-1)
        overview_fft_src = generate_fft_image_src(-1)

        # Datatable contents
        datatable_contents = data.to_datatable_format(columns_of_interest)

        return new_count_str, overview_figure, motion_figure, ctf_figure, overview_micrograph_src, overview_fft_src,\
               datatable_contents
    else:
        raise PreventUpdate


@app.callback([Output('details_table', 'style_data_conditional'),
               Output('details_real', 'src'),
               Output('details_fft', 'src'),
               Output('details_avrot', 'src'),
               Output('interval-component', 'n_intervals')],
              [Input('details_table', 'selected_rows')])
def row_selected_updater(selected_rows):
    # Guard against callback sequence not having anything in `data.data` yet
    global data
    if data is None or data.data is None:
        raise PreventUpdate

    # Note that, unlike plotly, Dash indices do start at 0
    new_selector = [{'if': {'row_index': i}, 'background_color': '#D2F3FF'} for i in selected_rows]
    # Try first without triggering a massive update, but if this worker hasn't updated, then fire the interval-component
    # by resetting it to 0 so that new info from `data.update` can be synced to all components
    interval_state = dash.no_update
    try:
        details_real_src = generate_mic_image_src(selected_rows[0])
        details_fft_src = generate_fft_image_src(selected_rows[0])
        details_avrot_src = generate_avrot_image_src(selected_rows[0])
    except IndexError as error:
        if data.update():
            details_real_src = generate_mic_image_src(selected_rows[0])
            details_fft_src = generate_fft_image_src(selected_rows[0])
            details_avrot_src = generate_avrot_image_src(selected_rows[0])
            interval_state = 0
        else:
            raise error
    return new_selector, details_real_src, details_fft_src, details_avrot_src, interval_state


@app.callback([Output('overview_modal', 'style'),
               Output('overview_modal_img', 'src')],
              [Input('overview_real', 'n_clicks'),
               Input('overview_fft', 'n_clicks')],
              [State('overview_real', 'src'),
               State('overview_fft', 'src'),
               State('overview_modal', 'style')])
def overview_modal_on(overview_mic_clicks, overview_fft_clicks,
                      overview_mic_src, overview_fft_src, modal_container_style):
    if modal_container_style is None:
        modal_container_style = {}
    if overview_mic_clicks or overview_fft_clicks:
        modal_container_style['display'] = 'block'
        return modal_container_style, overview_mic_src if overview_mic_clicks else overview_fft_src
    else:
        modal_container_style['display'] = 'none'
        return modal_container_style, None


@app.callback([Output('details_modal', 'style'),
               Output('details_modal_img', 'src')],
              [Input('details_real', 'n_clicks'),
               Input('details_fft', 'n_clicks'),
               Input('details_avrot', 'n_clicks')],
              [State('details_real', 'src'),
               State('details_fft', 'src'),
               State('details_avrot', 'src'),
               State('details_modal', 'style')])
def details_modal_on(details_mic_clicks, details_fft_clicks, details_avrot_clicks,
                     details_mic_src, details_fft_src, details_avrot_src, container_style):
    if container_style is None:
        container_style = {}
    if details_mic_clicks or details_fft_clicks or details_avrot_clicks:
        container_style['display'] = 'block'
        if details_mic_clicks:
            modal_src = details_mic_src
        elif details_fft_clicks:
            modal_src = details_fft_src
        else:
            modal_src = details_avrot_src
        return container_style, modal_src
    else:
        container_style['display'] = 'none'
        return container_style, None


@app.callback([Output('overview_real', 'n_clicks'),
               Output('overview_fft', 'n_clicks')],
              [Input('overview_modal', 'n_clicks')])
def close_overview_modal(n):
    return 0, 0


@app.callback([Output('details_real', 'n_clicks'),
               Output('details_fft', 'n_clicks'),
               Output('details_avrot', 'n_clicks')],
              [Input('details_modal', 'n_clicks')])
def close_details_modal(n):
    return 0, 0, 0


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
    app.title = 'mvf: ' + os.path.split(project_dir)[-1]


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
