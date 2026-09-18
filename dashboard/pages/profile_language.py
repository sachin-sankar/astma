"""Profile Language & Topic Modeling Page for Dash Application."""

import dash
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
from dash import Input, Output, callback, dash_table, dcc, html

from src.common.config import DEFAULT_CONFIG

dash.register_page(
    __name__,
    path="/profile-language",
    name="Profile Language",
    title="Profile Language | Analytics",
)


def load_text_data():
    terms_df = pd.read_parquet(DEFAULT_CONFIG.text_terms_parquet)
    topics_df = pd.read_parquet(DEFAULT_CONFIG.topics_parquet)
    return terms_df, topics_df


def layout():
    terms_df, topics_df = load_text_data()

    # Top High Earner terms vs Non-High Earner terms
    top_high_terms = terms_df.head(15).sort_values("log_diff_score", ascending=True)
    fig_high_terms = px.bar(
        top_high_terms,
        x="log_diff_score",
        y="term",
        orientation="h",
        title="Top 15 High-Earner Differential Terms (TF-IDF Log-Odds)",
        labels={
            "log_diff_score": "Log Differential Prominence",
            "term": "Keyword / Bigram",
        },
        color="log_diff_score",
        color_continuous_scale="Greens",
    )
    fig_high_terms.update_layout(
        template="plotly_white",
        margin=dict(l=20, r=20, t=40, b=20),
        coloraxis_showscale=False,
    )

    top_non_high_terms = (
        terms_df.sort_values("log_diff_score", ascending=True)
        .head(15)
        .sort_values("log_diff_score", ascending=False)
    )
    fig_non_high_terms = px.bar(
        top_non_high_terms,
        x="log_diff_score",
        y="term",
        orientation="h",
        title="Top 15 Non-High-Earner Differential Terms",
        labels={
            "log_diff_score": "Log Differential Prominence",
            "term": "Keyword / Bigram",
        },
        color="log_diff_score",
        color_continuous_scale="Reds_r",
    )
    fig_non_high_terms.update_layout(
        template="plotly_white",
        margin=dict(l=20, r=20, t=40, b=20),
        coloraxis_showscale=False,
    )

    # Topics Bar Chart
    fig_topics = px.bar(
        topics_df.sort_values("high_earner_rate", ascending=True),
        x="high_earner_rate",
        y="topic_label",
        orientation="h",
        title="LDA Topics Ranked by High-Earner Concentration",
        labels={
            "high_earner_rate": "High-Earner Rate (%)",
            "topic_label": "Topic Label",
        },
        color="median_earnings",
        color_continuous_scale="Viridis",
    )
    fig_topics.update_layout(
        template="plotly_white",
        margin=dict(l=20, r=20, t=40, b=20),
    )

    # Topic Cards
    topic_cards = []
    for _, trow in topics_df.iterrows():
        topic_cards.append(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.H6(
                                trow["topic_label"],
                                className="fw-bold text-primary mb-1",
                            ),
                            html.Div(
                                [
                                    dbc.Badge(
                                        f"{trow['high_earner_rate'] * 100:.1f}% High Earners",
                                        color="success",
                                        className="me-1",
                                    ),
                                    dbc.Badge(
                                        f"${trow['median_earnings']:,.0f} Median",
                                        color="info",
                                        className="me-1",
                                    ),
                                    dbc.Badge(
                                        f"{trow['dominant_freelancer_count']:,} Freelancers",
                                        color="secondary",
                                    ),
                                ],
                                className="mb-2",
                            ),
                            html.P(
                                trow["top_keywords"], className="small text-muted mb-0"
                            ),
                        ]
                    ),
                    className="shadow-sm border-0 mb-3 h-100",
                ),
                md=6,
            )
        )

    return html.Div(
        [
            html.Div(
                [
                    html.H2(
                        "Profile Language & Topic Modeling",
                        className="fw-bold text-dark",
                    ),
                    html.P(
                        "Comparative NLP vocabulary extraction (Differential TF-IDF) and Latent Dirichlet Allocation (LDA) topic discovery across freelancer portfolios and descriptions.",
                        className="text-muted",
                    ),
                ],
                className="mb-4",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [dcc.Graph(figure=fig_high_terms, responsive=True)]
                            ),
                            className="shadow-sm border-0 mb-4",
                        ),
                        md=6,
                    ),
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [dcc.Graph(figure=fig_non_high_terms, responsive=True)]
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
                                [dcc.Graph(figure=fig_topics, responsive=True)]
                            ),
                            className="shadow-sm border-0 mb-4",
                        ),
                        md=12,
                    )
                ]
            ),
            html.H4(
                "Discovered Latent Topic Archetypes", className="fw-bold mb-3 text-dark"
            ),
            dbc.Row(topic_cards),
        ]
    )
