"""Skill Network Graph Page with Louvain Communities and Centrality."""

import dash
import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Input, Output, callback, dash_table, dcc, html

from src.common.config import DEFAULT_CONFIG

dash.register_page(
    __name__, path="/skill-network", name="Skill Network", title="Skill Network | Graph"
)


def load_network_data():
    nodes_df = pd.read_parquet(DEFAULT_CONFIG.network_nodes_parquet)
    edges_df = pd.read_parquet(DEFAULT_CONFIG.network_edges_parquet)
    comm_df = pd.read_parquet(DEFAULT_CONFIG.network_communities_parquet)
    return nodes_df, edges_df, comm_df


def layout():
    nodes_df, edges_df, comm_df = load_network_data()

    community_options = [{"label": "All Communities", "value": "all"}] + [
        {"label": f"Community {cid}: {row['top_skills']}", "value": int(cid)}
        for cid, row in comm_df.set_index("community_id").iterrows()
    ]

    controls = dbc.Card(
        dbc.CardBody(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.Label(
                                    "Filter Community:", className="fw-bold small"
                                ),
                                dcc.Dropdown(
                                    id="net-comm-filter",
                                    options=community_options,
                                    value="all",
                                    clearable=False,
                                ),
                            ],
                            md=4,
                        ),
                        dbc.Col(
                            [
                                html.Label(
                                    "Color Nodes By:", className="fw-bold small"
                                ),
                                dbc.RadioItems(
                                    id="net-color-mode",
                                    options=[
                                        {
                                            "label": "Louvain Community",
                                            "value": "community_id",
                                        },
                                        {
                                            "label": "High-Earner Rate",
                                            "value": "high_earner_rate",
                                        },
                                        {
                                            "label": "Bridge Score",
                                            "value": "bridge_score",
                                        },
                                    ],
                                    value="community_id",
                                    inline=True,
                                    className="mt-1",
                                ),
                            ],
                            md=4,
                        ),
                        dbc.Col(
                            [
                                html.Label(
                                    "Min Edge Weight Threshold:",
                                    className="fw-bold small",
                                ),
                                dcc.Slider(
                                    id="net-edge-weight-slider",
                                    min=50,
                                    max=500,
                                    step=50,
                                    value=150,
                                    marks={
                                        50: "50",
                                        150: "150",
                                        300: "300",
                                        500: "500",
                                    },
                                ),
                            ],
                            md=4,
                        ),
                    ],
                    className="align-items-center",
                )
            ]
        ),
        className="shadow-sm border-0 mb-4 bg-white",
    )

    # Bridge Skills Table
    bridge_skills = (
        nodes_df.sort_values("bridge_score", ascending=False)
        .head(10)[
            [
                "skill_name",
                "community_id",
                "freelancer_count",
                "betweenness_centrality",
                "bridge_score",
                "high_earner_rate",
            ]
        ]
        .copy()
    )
    bridge_skills["high_earner_rate"] = bridge_skills["high_earner_rate"].apply(
        lambda v: f"{v * 100:.1f}%"
    )

    bridge_table = dash_table.DataTable(
        columns=[
            {"name": col.replace("_", " ").title(), "id": col}
            for col in bridge_skills.columns
        ],
        data=bridge_skills.to_dict("records"),
        style_table={"overflowX": "auto"},
        style_cell={"fontSize": "12px", "textAlign": "left", "padding": "6px"},
        style_header={"backgroundColor": "#f8f9fa", "fontWeight": "bold"},
        style_as_list_view=True,
    )

    return html.Div(
        [
            html.Div(
                [
                    html.H2(
                        "Skill Co-Occurrence Network & Community Detection",
                        className="fw-bold text-dark",
                    ),
                    html.P(
                        "Force-directed topological graph partitioned using the Louvain modularity algorithm to uncover skill ecosystems and bridge nodes.",
                        className="text-muted",
                    ),
                ],
                className="mb-4",
            ),
            controls,
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.H5(
                                        "Interactive Force-Directed Network Graph",
                                        className="fw-bold mb-3",
                                    ),
                                    dcc.Graph(
                                        id="network-graph",
                                        style={"height": "650px"},
                                        responsive=True,
                                    ),
                                ]
                            ),
                            className="shadow-sm border-0 mb-4",
                        ),
                        md=8,
                    ),
                    dbc.Col(
                        [
                            dbc.Card(
                                dbc.CardBody(
                                    [
                                        html.H5(
                                            "Top Bridge Skills",
                                            className="fw-bold mb-2",
                                        ),
                                        html.P(
                                            "Skills connecting disparate functional communities (ranked by betweenness/degree ratio):",
                                            className="text-muted small",
                                        ),
                                        bridge_table,
                                    ]
                                ),
                                className="shadow-sm border-0 mb-4",
                            ),
                            dbc.Card(
                                dbc.CardBody(
                                    [
                                        html.H5(
                                            "Community Clusters Overview",
                                            className="fw-bold mb-2",
                                        ),
                                        html.Div(id="community-info-container"),
                                    ]
                                ),
                                className="shadow-sm border-0 mb-4",
                            ),
                        ],
                        md=4,
                    ),
                ]
            ),
        ]
    )


@callback(
    [Output("network-graph", "figure"), Output("community-info-container", "children")],
    [
        Input("net-comm-filter", "value"),
        Input("net-color-mode", "value"),
        Input("net-edge-weight-slider", "value"),
    ],
)
def update_network(selected_comm, color_mode, min_edge_weight):
    nodes_df, edges_df, comm_df = load_network_data()

    # Filter nodes if community selected
    if selected_comm != "all":
        target_nodes = set(
            nodes_df[nodes_df["community_id"] == int(selected_comm)]["skill_name"]
        )
        sub_nodes_df = nodes_df[nodes_df["community_id"] == int(selected_comm)].copy()
        sub_edges_df = edges_df[
            (edges_df["source"].isin(target_nodes))
            & (edges_df["target"].isin(target_nodes))
            & (edges_df["weight"] >= (min_edge_weight or 100))
        ].copy()
    else:
        target_nodes = set(nodes_df["skill_name"])
        sub_nodes_df = nodes_df.copy()
        sub_edges_df = edges_df[edges_df["weight"] >= (min_edge_weight or 100)].copy()

    node_pos = {
        row["skill_name"]: (row["x"], row["y"]) for _, row in sub_nodes_df.iterrows()
    }

    # Edge Traces
    edge_x = []
    edge_y = []
    for _, edge in sub_edges_df.iterrows():
        if edge["source"] in node_pos and edge["target"] in node_pos:
            x0, y0 = node_pos[edge["source"]]
            x1, y1 = node_pos[edge["target"]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        line=dict(width=0.6, color="#bdc3c7"),
        hoverinfo="none",
        mode="lines",
    )

    # Node Trace
    node_x = sub_nodes_df["x"].tolist()
    node_y = sub_nodes_df["y"].tolist()
    node_names = sub_nodes_df["skill_name"].tolist()
    node_sizes = (np.sqrt(sub_nodes_df["freelancer_count"]) * 1.5 + 8).tolist()

    hover_texts = [
        f"<b>{r['skill_name']}</b><br>Community: {r['community_id']}<br>Freelancers: {r['freelancer_count']:,}<br>High-Earner Rate: {r['high_earner_rate'] * 100:.1f}%<br>Median Rate: ${r['median_hourly_rate']}/hr<br>Bridge Score: {r['bridge_score']:.3f}"
        for _, r in sub_nodes_df.iterrows()
    ]

    # Color mapping
    if color_mode == "community_id":
        color_vals = sub_nodes_df["community_id"].astype(str)
        colorscale = "tab10"
        show_colorbar = False
    elif color_mode == "high_earner_rate":
        color_vals = sub_nodes_df["high_earner_rate"]
        colorscale = "Viridis"
        show_colorbar = True
    else:
        color_vals = sub_nodes_df["bridge_score"]
        colorscale = "Hot"
        show_colorbar = True

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers+text",
        hoverinfo="text",
        text=node_names,
        textposition="top center",
        textfont=dict(size=9, color="#2c3e50"),
        hovertext=hover_texts,
        marker=dict(
            showscale=show_colorbar,
            colorscale=colorscale,
            color=color_vals,
            size=node_sizes,
            line_width=1.5,
            line_color="white",
            colorbar=dict(
                thickness=15,
                title=color_mode.replace("_", " ").title(),
                xanchor="left",
                titleside="right",
            )
            if show_colorbar
            else None,
        ),
    )

    fig = go.Figure(
        data=[edge_trace, node_trace],
        layout=go.Layout(
            showlegend=False,
            hovermode="closest",
            margin=dict(b=10, l=10, r=10, t=10),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor="white",
            paper_bgcolor="white",
        ),
    )

    # Community Info Cards
    comm_cards = []
    for _, crow in comm_df.iterrows():
        cid = crow["community_id"]
        comm_cards.append(
            dbc.Alert(
                [
                    html.Strong(f"Community {cid}"),
                    html.Div(
                        f"{crow['num_skills']} skills • {crow['total_freelancers']:,} members • {crow['avg_high_earner_rate'] * 100:.1f}% high-earners",
                        className="small text-muted mb-1",
                    ),
                    html.Div(crow["top_skills"], className="small text-dark"),
                ],
                color="light",
                className="mb-2 p-2 border",
            )
        )

    return fig, html.Div(comm_cards)
