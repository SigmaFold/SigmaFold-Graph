"""
1. Gets all sequence data for a given n. Saves it locally for later use, in case the database is not available.
Save as pickle file.
2. Iterate through all elements. Every type a new shape_mapping is encountered, create the node and add it to the graph.
3. for every sequence, and an edge between all the shappe_mappings that it maps to.
4. Save the graph as a pickle file.
5. Display in a WEB UI using Dash.
"""
# Graph logic and data loading
import pandas as pd
import networkx as nx


import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from library.db_query_templates import get_all_sequence_data, get_all_shape_data
from library.shape_helper import deserialize_shape
from graph_logic import *

import os
import pickle

import pandas as pd
import plotly.express as px

import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc



# Use the Dash app to serve the figure

# set initial figure
initial_fig, initial_shape_ids, initial_shape_matrices, initial_shapes_df, initial_sequences_df = create_network_graph(10)

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.Img(src='/assets/SigmaFold_logo.png', alt='SigmaFold', style={'width': '400px', 'display': 'block', 'margin-left': 'auto', 'margin-right': 'auto'}), width=12)
    ]),

    dbc.Row([
        dbc.Col([
    
            html.H5("Select length of the chain (n)."),
            dcc.Slider(
                id='n-slider',
                min=MIN_N,
                max=MAX_N,
                step=1,
                value=INITIAL_N,
                marks={i: f'{i}' for i in range(MIN_N, MAX_N + 1)}
            ),
            html.Br(),
            html.Button('Update Graph', id='update-graph-button', n_clicks=0),
            dcc.Graph(id='graph', figure=initial_fig),
            dcc.Loading(
                id="loading",
                type="circle",
                children=[html.Div(id="loading-output")]
            )
        ]),
        dbc.Col([
            html.Div([
                html.Img(id='hover-image', src=''),
                html.Pre(id='hover-data')
            ])
        ])
  
    ]),
dcc.Store(id='stored-shape-ids', data=initial_shape_ids),
dcc.Store(id='stored-shape-matrices', data=initial_shape_matrices),
dcc.Store(id='stored-shapes-df', data=initial_shapes_df.to_json(date_format='iso', orient='split')),
dcc.Store(id='stored-sequences-df', data=initial_sequences_df.to_json(date_format='iso', orient='split'))

])

@app.callback(
    Output('graph', 'figure'),
    Output('hover-image', 'src'),
    Output('hover-data', 'children'),
    Output('stored-shape-ids', 'data'),
    Output('stored-shape-matrices', 'data'),
    Output('stored-shapes-df', 'data'),
    Output('loading-output', 'children'),
    Input('update-graph-button', 'n_clicks'),
    Input('graph', 'hoverData'),
    State('n-slider', 'value'),
    State('stored-shape-ids', 'data'),
    State('stored-shape-matrices', 'data'),
    State('stored-shapes-df', 'data'),
    State('stored-sequences-df', 'data')
)
def update_graph_and_hover_data(n_clicks, hover_data, n_value, shape_ids, shape_matrices_json, shapes_df_json, sequences_df_json):
    ctx = dash.callback_context
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if triggered_id == 'update-graph-button':
        fig, shape_ids, shape_matrices, shapes_df, sequences_df = create_network_graph(n_value)
        shape_matrices_list = {k: v.tolist() for k, v in shape_matrices.items()}  # Convert numpy arrays to lists
        print(f'n: {n_value}, sequences_df shape: {sequences_df.shape}, unique shape_ids: {sequences_df["shape_mapping"].nunique()}')

        return fig, dash.no_update, dash.no_update, shape_ids, shape_matrices_list, shapes_df.to_json(date_format='iso', orient='split'), None
    elif triggered_id == 'graph' and hover_data is not None and shape_ids is not None and shape_matrices_json is not None and shapes_df_json is not None:
        shape_matrices = {k: np.array(v) for k, v in shape_matrices_json.items()}  # Convert back to numpy arrays
        point_index = hover_data['points'][0]['pointIndex']
        shape_id = shape_ids[point_index]
        image_path = f'{shape_id}.png'
        save_image(shape_matrices[shape_id], image_path)
        # get all sequences for shape_id in sequences_df
        sequences_df = pd.read_json(sequences_df_json, orient='split')
        # reset column hea

        sequences = sequences_df[sequences_df['shape_mapping'] == shape_id]
        # convert to string with newline characters
        sequences_str = '\n'.join(sequences['sequence'].values)
        
        shapes_df = pd.read_json(shapes_df_json, orient='split')
        shape_data = shapes_df[shapes_df['shape_id'] == shape_id].iloc[0]
        hover_data_text = f'\n'.join([f'{col}: {val}' for col, val in shape_data.items()])
        # add sequences to hover_data_text
        hover_data_text += f'\nSequences:\n{sequences_str}'


        
        return dash.no_update, f'/assets/{image_path}', hover_data_text, dash.no_update, dash.no_update, dash.no_update, None
    return dash.no_update, '', '', dash.no_update, dash.no_update, dash.no_update, None


if __name__ == '__main__':
    app.run_server(debug=True)
