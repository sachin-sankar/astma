"""Skill Bundles Analysis Page for Dash Application."""

import json

import dash
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
from dash import Input, Output, callback, dash_table, dcc, html

from src.common.config import DEFAULT_CONFIG

dash.register_page(
    __name__,
    path="/skill-bundles",
    name="Skill Bundles",
    title="Skill Bundles | Analytics",
)


def load_bundles_data():
    df = pd.read_parquet(DEFAULT_CONFIG.skill_combinations_parquet)
    with open(DEFAULT_CONFIG.combination_regression_json, "r", encoding="utf-8") as f:
        reg_data = json.load(f)
    return df, reg_data


def layout():
    df, reg_data = load_bundles_data()

    # Get unique skills for dropdown filter
    all_skills_list = sorted(
        list(
            set(
                [
                    skill
                    for sublist in df["bundle_skills"].apply(json.loads).head(1000)
                    for skill in sublist
                ]
            )
        )
    )

    controls = dbc.Card(
        dbc.CardBody(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.Label(
                                    "Filter by Skill:", className="fw-bold small"
                                ),
                                dcc.Dropdown(
                                    id="bundle-skill-filter",
                                    options=[
                                        {"label": s, "value": s}
                                        for s in all_skills_list
                                    ],
                                    placeholder="Select a skill...",
                                    clearable=True,
                                ),
                            ],
                            md=4,
                        ),
                        dbc.Col(
                            [
                                html.Label("Bundle Size:", className="fw-bold small"),
                                dbc.RadioItems(
                                    id="bundle-size-filter",
                                    options=[
                                        {"label": "All Sizes", "value": "all"},
                                        {"label": "Pairs Only (2)", "value": 2},
                                        {"label": "Triples Only (3)", "value": 3},
                                    ],
                                    value="all",
                                    inline=True,
                                    className="mt-1",
                                ),
                            ],
                            md=4,
                        ),
                        dbc.Col(
                            [
                                html.Label(
                                    "Min Freelancers (Support Count):",
                                    className="fw-bold small",
                                ),
                                dcc.Slider(
                                    id="bundle-min-count-slider",
                                    min=20,
                                    max=200,
                                    step=10,
                                    value=30,
                                    marks={20: "20", 50: "50", 100: "100", 200: "200"},
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

    # Regression View Card
    reg_df = pd.DataFrame(reg_data["top_bundles_regression"])
    fig_regression = px.scatter(
        reg_df.head(15),
        x="controlled_odds_ratio",
        y="bundle_name",
        error_x="controlled_ci_upper",
        error_x_minus="controlled_ci_lower",
        orientation="h",
        title="Controlled Odds Ratios (Controlling for Skill Count, Reviews & Country)",
        labels={
            "controlled_odds_ratio": "Adjusted Odds Ratio (with 95% CI)",
            "bundle_name": "Skill Bundle",
        },
        color="ols_log_earnings_coef",
        color_continuous_scale="Viridis",
    )
    fig_regression.update_layout(
        template="plotly_white",
        margin=dict(l=20, r=20, t=40, b=20),
        yaxis=dict(autorange="reversed"),
    )

    return html.Div(
        [
            html.Div(
                [
                    html.H2(
                        "Skill Combinations & Earnings Disproportion",
                        className="fw-bold text-dark",
                    ),
                    html.P(
                        "Examine frequent itemsets (pairs and triples), their statistical associations with the top 10% earnings tier, and FDR-corrected significance.",
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
                                        "Bundle Association Scatter Matrix",
                                        className="fw-bold mb-3",
                                    ),
                                    dcc.Graph(
                                        id="bundle-scatter-plot", responsive=True
                                    ),
                                ]
                            ),
                            className="shadow-sm border-0 mb-4",
                        ),
                        md=12,
                    )
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.H5(
                                        "Controlled Econometric Effect Sizes",
                                        className="fw-bold mb-3",
                                    ),
                                    dcc.Graph(figure=fig_regression, responsive=True),
                                ]
                            ),
                            className="shadow-sm border-0 mb-4",
                        ),
                        md=6,
                    ),
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.H5(
                                        "Interactive Combinations DataTable",
                                        className="fw-bold mb-3",
                                    ),
                                    html.Div(id="bundle-table-container"),
                                ]
                            ),
                            className="shadow-sm border-0 mb-4",
                        ),
                        md=6,
                    ),
                ]
            ),
        ]
    )


@callback(
    [
        Output("bundle-scatter-plot", "figure"),
        Output("bundle-table-container", "children"),
    ],
    [
        Input("bundle-skill-filter", "value"),
        Input("bundle-size-filter", "value"),
        Input("bundle-min-count-slider", "value"),
    ],
)
def update_bundles(selected_skill, size_filter, min_count):
    df = pd.read_parquet(DEFAULT_CONFIG.skill_combinations_parquet)

    filtered = df[df["freelancer_count"] >= (min_count or 20)].copy()

    if size_filter != "all":
        filtered = filtered[filtered["bundle_size"] == int(size_filter)]

    if selected_skill:
        filtered = filtered[
            filtered["bundle_name"].str.contains(
                selected_skill, case=False, regex=False
            )
        ]

    filtered = filtered.head(250)

    # Scatter Plot: Lift vs High Earner Rate
    fig_scatter = px.scatter(
        filtered,
        x="lift",
        y="high_earner_rate",
        size="freelancer_count",
        color="odds_ratio",
        hover_name="bundle_name",
        hover_data={
            "freelancer_count": True,
            "support": ":.4f",
            "odds_ratio": ":.2f",
            "adjusted_p_value": ":.2e",
        },
        labels={
            "lift": "Co-occurrence Lift",
            "high_earner_rate": "High-Earner Proportion",
            "odds_ratio": "Odds Ratio",
        },
        color_continuous_scale="Plasma",
    )
    fig_scatter.update_layout(
        template="plotly_white",
        margin=dict(l=20, r=20, t=20, b=20),
    )

    # Table
    table_cols = [
        {"name": "Skill Bundle", "id": "bundle_name"},
        {"name": "Size", "id": "bundle_size"},
        {"name": "Count", "id": "freelancer_count"},
        {"name": "Lift", "id": "lift"},
        {"name": "High %", "id": "high_earner_rate"},
        {"name": "OR", "id": "odds_ratio"},
        {"name": "FDR p-val", "id": "adjusted_p_value"},
    ]

    table_data = filtered.head(50).to_dict("records")
    for r in table_data:
        r["high_earner_rate"] = f"{r['high_earner_rate'] * 100:.1f}%"
        r["adjusted_p_value"] = f"{r['adjusted_p_value']:.2e}"

    table = dash_table.DataTable(
        columns=table_cols,
        data=table_data,
        page_size=10,
        style_table={"overflowX": "auto"},
        style_cell={"fontSize": "12px", "textAlign": "left", "padding": "6px"},
        style_header={"backgroundColor": "#f8f9fa", "fontWeight": "bold"},
        style_as_list_view=True,
    )

    return fig_scatter, table
