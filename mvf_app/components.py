import cryoemtools.relionstarparser as rsp
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots


motion_columns = ['rlnAccumMotionEarly', 'rlnAccumMotionLate', 'rlnAccumMotionTotal']
motion_columns_text = ['Whole-frame motion during first 4 e-/Å² (Å)',
                       'Whole-frame motion during remainder of movie (Å)',
                       'Total whole-frame motion (Å)']
ctf_columns = ['rlnDefocusU', 'rlnCtfAstigmatism', 'rlnCtfFigureOfMerit', 'rlnCtfMaxResolution']
ctf_columns_text = ['Defocus (Å)', 'Astigmatism (Å)', 'CTF fit figure of merit', 'CTF fit resolution (Å)']

columns_of_interest = motion_columns + ctf_columns
columns_text = motion_columns_text + ctf_columns_text
columns_text_map = dict(zip(columns_of_interest, columns_text))

####
#
# Construct a template (starting with the plotly default) to use as a base theme
#
my_plotly_template = go.layout.Template(pio.templates[pio.templates.default])
my_plotly_template.data.scatter = [go.Scatter(mode='lines+markers',
                                              line={'width': 2},
                                              marker={'size': 8})]
my_plotly_template.layout.xaxis.update(title_font_size=12, title_standoff=0, automargin=True)
my_plotly_template.layout.yaxis.update(title_font_size=12, title_standoff=6, automargin=True)
my_plotly_template.layout.update(margin=go.layout.Margin(l=25, r=25, t=25, b=25))

# Give every column a unique color
column_colormap = dict(zip(columns_of_interest, my_plotly_template['layout']['colorway']))


####
#
# Plots!
#
overview_figure = make_subplots(rows=len(columns_of_interest), cols=1, shared_xaxes=True, vertical_spacing=0.04,
                                subplot_titles=columns_text)
overview_figure.update_layout(template=my_plotly_template, showlegend=False)
overview_figure.update_xaxes(title_text="Exposure number", row=len(columns_of_interest))
# Plotly's API frustratingly clobbers any attempts at dictating subplot title location or font in the template
for subplot_title in overview_figure.layout.annotations:
    subplot_title.font.size = 12
    subplot_title.xanchor = 'left'
    subplot_title.x = 0.0
for i,column in enumerate(columns_of_interest):
    overview_figure.add_trace(go.Scatter(y=[], name=column, marker_color=column_colormap[column],
                                         line_color=column_colormap[column], meta={'y': column}),
                              row=i+1, col=1)


motion_figure = make_subplots(rows=2, cols=3, horizontal_spacing=0.04, vertical_spacing=0.09,
                              specs=[[{'colspan': 3}, None, None],
                                     [{}, {}, {}]])
motion_figure.update_layout(template=my_plotly_template, legend_orientation="h",
                            legend=dict(x=0.0, y=1.0, xanchor='left', yanchor='bottom'))
motion_figure.update_yaxes(title_text="Counts", row=2, col=1)
motion_figure.update_xaxes(title_text="Exposure number", row=1)
for i, motion_col in enumerate(motion_columns):
    motion_figure.add_trace(go.Scatter(y=[], name=columns_text_map[motion_col],
                                       legendgroup=columns_text_map[motion_col],
                                       marker_color=column_colormap[motion_col],
                                       line_color=column_colormap[motion_col],
                                       meta={'y': motion_col}),
                            row=1, col=1)
    motion_figure.add_trace(go.Histogram(x=[], name=columns_text_map[motion_col],
                                         legendgroup=columns_text_map[motion_col], showlegend=False,
                                         marker_color=column_colormap[motion_col],
                                         meta={'x': motion_col}),
                            row=2, col=i+1)
    motion_figure.update_xaxes(title_text=columns_text_map[motion_col], row=2, col=i+1)


len_ctf_columns = len(ctf_columns)
ctf_plot_row_count = len_ctf_columns + (len_ctf_columns // 3) * 2 + (len_ctf_columns % 3 > 0) * 2
ctf_figure = make_subplots(rows=ctf_plot_row_count, cols=3, horizontal_spacing=0.04, vertical_spacing=0.06,
                           specs=[[{'colspan': 3}, None, None]] * len_ctf_columns +
                                 [[{'rowspan': 2}, {'rowspan': 2}, {'rowspan': 2}], [None, None, None]] *
                                    (len_ctf_columns//3) +
                                 [[{'rowspan': 2}] * (len_ctf_columns%3) + [None] * (3-(len_ctf_columns%3))] +
                                 [[None, None, None]])
ctf_figure.update_layout(template=my_plotly_template, legend_orientation="h",
                         legend=dict(x=0.0, y=1.0, xanchor='left', yanchor='bottom'))
for i in range(len_ctf_columns, ctf_plot_row_count, 2):
    ctf_figure.update_yaxes(title_text="Counts", row=i+1, col=1)
for i, ctf_col in enumerate(ctf_columns):
    ctf_figure.update_xaxes(title_text="Exposure number", row=i+1)
    ctf_figure.add_trace(go.Scatter(y=[], name=columns_text_map[ctf_col],
                                    legendgroup=columns_text_map[ctf_col],
                                    marker_color=column_colormap[ctf_col],
                                    line_color=column_colormap[ctf_col],
                                    meta={'y': ctf_col}),
                         row=i+1, col=1)
    hist_row = len_ctf_columns + (i // 3) * 2
    hist_col = i % 3
    ctf_figure.add_trace(go.Histogram(x=[], name=columns_text_map[ctf_col],
                                      legendgroup=columns_text_map[ctf_col], showlegend=False,
                                      marker_color=column_colormap[ctf_col],
                                      meta={'x': ctf_col}),
                         row=hist_row+1, col=hist_col+1)
    ctf_figure.update_xaxes(title_text=columns_text_map[ctf_col], row=hist_row+1, col=hist_col+1)


def update_figures(new_data):
    for trace in overview_figure.data + motion_figure.data + ctf_figure.data:
        for axis in trace.meta:
            trace.__setattr__(axis, new_data[trace.meta[axis]])


if __name__ == '__main__':
    '''
    For testing purposes, this file can be run directly with hard-coded testing data .star file
    '''
    with open('/Users/James/PycharmProjects/mvf/testing/External/job004/micrographs.star', 'r') as fh:
        data = rsp.read(fh, parseonly=['micrographs'], flatten=True)
    update_figures(data)
    overview_figure.show()
    motion_figure.show()
    ctf_figure.show()
