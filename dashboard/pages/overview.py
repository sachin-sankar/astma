"""Overview Page for Skill Bundles and Freelancer Earnings Dashboard."""

import json
from pathlib import Path

import dash
import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import dcc, html

from src.common.config import DEFAULT_CONFIG

dash.register_page(
    __name__, path="/", name="Overview", title="Overview | Skill Bundles"
)

DATA_DIR = DEFAULT_CONFIG.analytical_dir


def load_data():
    with open(DEFAULT_CONFIG.overview_metrics_json, "r", encoding="utf-8") as f:
        overview = json.load(f)

    df_earnings = pd.read_parquet(DEFAULT_CONFIG.earnings_distribution_parquet)
    df_skills = pd.read_parquet(DEFAULT_CONFIG.skill_statistics_parquet)
    return overview, df_earnings, df_skills


def layout():
    overview, df_earnings, df_skills = load_data()

    # Cards
    kpi_cards = dbc.Row(
        [
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.H6(
                                "Total Freelancers",
                                className="text-muted text-uppercase small",
                            ),
                            html.H3(
                                f"{overview['total_freelancers']:,}",
                                className="text-primary fw-bold",
                            ),
                            html.Small(
                                f"{overview['total_unique_skills']:,} Unique Skills Cataloged",
                                className="text-muted",
                            ),
                        ]
                    ),
                    className="shadow-sm border-0 mb-3",
                ),
                md=3,
                sm=6,
            ),
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.H6(
                                "High-Earner Threshold (90th %)",
                                className="text-muted text-uppercase small",
                            ),
                            html.H3("$79,498", className="text-success fw-bold"),
                            html.Small(
                                f"{int(overview['total_high_earners'])} freelancers ({overview['high_earner_rate'] * 100:.1f}%)",
                                className="text-muted",
                            ),
                        ]
                    ),
                    className="shadow-sm border-0 mb-3",
                ),
                md=3,
                sm=6,
            ),
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.H6(
                                "Median Total Earnings",
                                className="text-muted text-uppercase small",
                            ),
                            html.H3(
                                f"${overview['median_earnings']:,.2f}",
                                className="text-info fw-bold",
                            ),
                            html.Small(
                                f"Mean: ${overview['mean_earnings']:,.2f}",
                                className="text-muted",
                            ),
                        ]
                    ),
                    className="shadow-sm border-0 mb-3",
                ),
                md=3,
                sm=6,
            ),
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.H6(
                                "Median Hourly Rate",
                                className="text-muted text-uppercase small",
                            ),
                            html.H3(
                                f"${overview['median_hourly_rate']:,.2f}/hr",
                                className="text-warning fw-bold",
                            ),
                            html.Small(
                                f"Mean: ${overview['mean_hourly_rate']:,.2f}/hr",
                                className="text-muted",
                            ),
                        ]
                    ),
                    className="shadow-sm border-0 mb-3",
                ),
                md=3,
                sm=6,
            ),
        ],
        className="mb-4",
    )

    # 1. Earnings Distribution Histogram (Log scale vs Raw)
    fig_earnings = px.histogram(
        df_earnings[df_earnings["total_earnings"] > 0],
        x="log_earnings",
        nbins=50,
        color="high_earner",
        color_discrete_map={True: "#2ecc71", False: "#3498db"},
        labels={"log_earnings": "Log(Earnings + 1)", "high_earner": "High Earner Tier"},
        title="Freelancer Earnings Distribution (Log Scale)",
    )
    fig_earnings.update_layout(
        template="plotly_white",
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    # 2. Skills per user histogram
    fig_skills_dist = px.histogram(
        df_earnings,
        x="skill_count",
        nbins=40,
        title="Distribution of Skills Selected Per Freelancer",
        color_discrete_sequence=["#e67e22"],
        labels={"skill_count": "Explicit User Skills Count"},
    )
    fig_skills_dist.update_layout(
        template="plotly_white",
        margin=dict(l=20, r=20, t=40, b=20),
    )

    # 3. Top Popular Skills vs Top High-Earning Skills
    top_popular = df_skills.head(15).sort_values("freelancer_count", ascending=True)
    fig_popular = px.bar(
        top_popular,
        x="freelancer_count",
        y="skill_name",
        orientation="h",
        title="Top 15 Most Prevalent Skills",
        labels={"freelancer_count": "Freelancer Count", "skill_name": "Skill"},
        color="freelancer_count",
        color_continuous_scale="Blues",
    )
    fig_popular.update_layout(
        template="plotly_white",
        margin=dict(l=20, r=20, t=40, b=20),
        coloraxis_showscale=False,
    )

    top_earning_skills = (
        df_skills[df_skills["freelancer_count"] >= 30]
        .sort_values("high_earner_rate", ascending=False)
        .head(15)
        .sort_values("high_earner_rate", ascending=True)
    )
    fig_earning_skills = px.bar(
        top_earning_skills,
        x="high_earner_rate",
        y="skill_name",
        orientation="h",
        title="Top 15 High-Earner Associated Skills (Min N>=30)",
        labels={"high_earner_rate": "High-Earner Rate (%)", "skill_name": "Skill"},
        color="high_earner_rate",
        color_continuous_scale="Greens",
    )
    fig_earning_skills.update_layout(
        template="plotly_white",
        margin=dict(l=20, r=20, t=40, b=20),
        coloraxis_showscale=False,
    )

    return html.Div(
        [
            html.Div(
                [
                    html.H2(
                        "Market Overview & Freelancer Demographics",
                        className="fw-bold text-dark",
                    ),
                    html.P(
                        "High-level empirical baseline across 10,002 verified freelancer profiles and 3,195 unique skills.",
                        className="text-muted",
                    ),
                ],
                className="mb-4",
            ),
            kpi_cards,
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [dcc.Graph(figure=fig_earnings, responsive=True)]
                            ),
                            className="shadow-sm border-0 mb-4",
                        ),
                        md=6,
                    ),
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [dcc.Graph(figure=fig_skills_dist, responsive=True)]
                            ),
                            className="shadow-sm border-0 mb-4",
                        ),
                        md=6,
                    ),
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [dcc.Graph(figure=fig_popular, responsive=True)]
                            ),
                            className="shadow-sm border-0 mb-4",
                        ),
                        md=6,
                    ),
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [dcc.Graph(figure=fig_earning_skills, responsive=True)]
                            ),
                            className="shadow-sm border-0 mb-4",
                        ),
                        md=6,
                    ),
                ]
            ),
        ]
    )
