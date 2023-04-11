# load each of the graphs 
from graph_logic import load_data_from_json
import networkx as nx
import json
import community 
import matplotlib.pyplot as plt
import networkx.algorithms.community as nx_comm
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import community
import numpy as np

from networkx.algorithms import community as nx_comm
import igraph as ig
import leidenalg
import pandas as pd
import plotly.offline as pyo
import plotly.express as px

# Louvain community detection
n = 13
G = nx.node_link_graph(load_data_from_json(f'data/graph_{n}.json'))

# Convert the graph to igraph format
G_ig = ig.Graph.from_networkx(G)

# use leidenalg to find the communities and plot
partition = leidenalg.find_partition(G_ig, leidenalg.ModularityVertexPartition)
print(partition)
print(partition.membership)
print(partition.q)



# plot
# remove edges
pos = nx.spring_layout(G)
# Convert nodes and edges to DataFrames
nodes_df = pd.DataFrame(pos, columns=["x", "y"]).reset_index().rename(columns={"index": "node"})
nodes_df["community"] = partition.membership

edges_df = pd.DataFrame(G.edges, columns=["source", "target"])

# Create custom discrete color scale
color_scale = px.colors.qualitative.Plotly
num_communities = len(set(partition.membership))
color_list = color_scale * (num_communities // len(color_scale) + 1)
color_discrete_map = {i: color_list[i] for i in range(num_communities)}

# Create scatter plot with custom hover data and colors
fig = pyo.scatter(
    nodes_df,
    color="community",
    color_discrete_map=color_discrete_map,
    hover_data=["node"],
    symbol_sequence=["circle"],
    size_max=10,
    title="Communities",
)

# Set plot background to white
fig.update_layout(
    plot_bgcolor="white",
    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
)

pyo.plot(fig, filename='communities_plot.html', auto_open=True)
fig.write_image("communities_plot.png")



    

