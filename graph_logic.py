from PIL import Image
import base64
import numpy as np
import networkx as nx
import pandas as pd
import json
import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from library.db_query_templates import get_all_sequence_data, get_all_shape_data
from library.shape_helper import deserialize_shape
import plotly.express as px
# save plot as pdf
import plotly.io as pio
# n value controls based on what is available in the database
MIN_N = 8
MAX_N = 14
INITIAL_N = 10


def save_data_to_json(data, file_path):
    with open(file_path, "w") as f:
        json.dump(data, f)

def load_data_from_json(file_path):
    with open(file_path, "r") as f:
        data = json.load(f, )
    return data

def create_network_graph(n):
        # Housekeeping to avoid re-running the same queries
    if os.path.exists(f'data/sequences_df_{n}.json') and os.path.exists(f'data/shapes_df_{n}.json'):
        # read data from json as dict convert to dataframe
        sequences_df = pd.read_json(f'data/sequences_df_{n}.json', orient='split', convert_dates=False)
        shapes_df = pd.read_json(f'data/shapes_df_{n}.json', orient='split', convert_dates=False)
    else:
        sequences_df = get_all_sequence_data(n)
        shapes_df = get_all_shape_data(n)
        sequences_df.to_json(f'data/sequences_df_{n}.json', orient='split')
        shapes_df.to_json(f'data/shapes_df_{n}.json', orient='split')


    # Define the correct order of columns
    correct_column_order = ['sequence_id', 'sequence', 'degeneracy', 'length', 'energy', 'shape_mapping', 'path']
    sequences_df = sequences_df[correct_column_order]

    
    # Housekeeping to avoid re-computing the entire graph every time
    graph_json_path = f'data/graph_{n}.json'
    if os.path.exists(graph_json_path):
        G = nx.node_link_graph(load_data_from_json(graph_json_path))

    else:
        G = nx.Graph()

        for shape_id in shapes_df['shape_id']:
            if len(shape_id) >= 2:
                G.add_node(shape_id)

        for _, group in sequences_df.groupby('sequence'):
            shape_mappings = group['shape_mapping'].tolist()
            for i in range(len(shape_mappings)):
                for j in range(i+1, len(shape_mappings)):
                    if G.has_edge(shape_mappings[i], shape_mappings[j]):
                        G[shape_mappings[i]][shape_mappings[j]]['weight'] += 1
                    else:
                        G.add_edge(shape_mappings[i], shape_mappings[j], weight=1)

        nodes_to_remove = []
        for node in G.nodes:
            if len(node) < 2:
                nodes_to_remove.append(node)
        G.remove_nodes_from(nodes_to_remove)

        save_data_to_json(nx.node_link_data(G), graph_json_path)


    # spring layout makes higher weights closer together
    pos = nx.spring_layout(G)
    shape_ids = list(G.nodes)
    xs = [pos[sid][0] for sid in shape_ids]
    ys = [pos[sid][1] for sid in shape_ids]
    shape_ids = [shape_id for shape_id in shape_ids if len(shape_id) >= 2]

    shape_matrices = {}
    for shape_id in shape_ids:
        try:
            matrix = deserialize_shape(shape_id)
            shape_matrices[shape_id] = matrix
        except:
            print("Error")
            print(shape_id)

    # Save the images and encode them as base64 strings
    base64_images = {}
    for shape_id, matrix in shape_matrices.items():
        image_path = save_image(matrix, f'{shape_id}.png')
        encoded_image = encode_image_base64(image_path)
        base64_images[shape_id] = encoded_image

    # Define node_colors
    node_colors = [G.degree(sid) for sid in shape_ids]

    fig = px.scatter(
        x=xs,
        y=ys,
        color=node_colors,
        color_continuous_scale='plasma',
        color_continuous_midpoint=0,
        hover_name=shape_ids,
        custom_data=[shape_ids],
        labels={'color': 'Degree'}
    )

    fig.update_traces(
        hovertemplate="Shape ID: %{customdata[0]}<br>X: %{x}<br>Y: %{y}"
    )

    fig.update_layout(
        autosize=False,
        width=900,
        height=900,
        title='Graph Visualization',
        xaxis=dict(title='X'),
        yaxis=dict(title='Y'),
        hovermode='closest',
        clickmode='event+select',
    )

    # Use the Dash app to serve the figure
    fig.update_layout(
        # remove x and y labels
        xaxis=dict(showticklabels=False),
        yaxis=dict(showticklabels=False),

        autosize=False,
        width=900,
        height=900,
        title=f"Graph Visualization (n={n})",
        hovermode='closest',
        clickmode='event+select',
    )
    print(f'n: {n}, sequences_df shape: {sequences_df.shape}, unique shape_ids: {sequences_df["shape_mapping"].nunique()}')
    pio.write_image(fig, f"graph_{n}.pdf")
    return fig, shape_ids, shape_matrices, shapes_df, sequences_df



def save_image(matrix, image_path):
    # Normalize the matrix values to range between 0 and 255
    normalized_matrix = (matrix * 255).astype(np.uint8)
    
    # Create an image object from the normalized matrix
    img = Image.fromarray(normalized_matrix, mode='L')
    img = img.resize((300, 300), Image.NEAREST)
    
    # Save the image
    img.save(f'assets/{image_path}')
    return f'assets/{image_path}'




def encode_image_base64(image_path):
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    return encoded_string



def save_all_pngs_to_assets(min_n=8, max_n=14):
    for n in range(min_n, max_n + 1):
        _, _, shape_matrices, _, _ = create_network_graph(n)
        for shape_id, matrix in shape_matrices.items():
            image_path = f"{shape_id}.png"
            save_image(matrix, image_path)


if __name__ == '__main__':
    try:
        save_all_pngs_to_assets(min_n=15, max_n=16)

    except Exception as e:
        print(e)
