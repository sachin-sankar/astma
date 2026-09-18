"""Geography Page for Dash Application."""

import dash
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
from dash import Input, Output, callback, dash_table, dcc, html

from src.common.config import DEFAULT_CONFIG

dash.register_page(
    __name__, path="/geography", name="Geography", title="Geography | Analytics"
)


def load_geo_data():
    country_df = pd.read_parquet(DEFAULT_CONFIG.geographic_statistics_parquet)
    city_path = DEFAULT_CONFIG.analytical_dir / "city_statistics.parquet"
    city_df = pd.read_parquet(city_path) if city_path.exists() else pd.DataFrame()
    return country_df, city_df


def layout():
    country_df, city_df = load_geo_data()

    # World Choropleth Map of Freelancers / High Earner Rates
    fig_map = px.choropleth(
        country_df,
        locations="country",
        locationmode="country names",
        color="high_earner_rate",
        hover_name="country",
        hover_data={
            "freelancer_count": True,
            "high_earner_rate": ":.2%",
            "median_earnings": ":$,.0f",
            "median_hourly_rate": ":$,.0f",
        },
        title="Global Geographic Distribution of High-Earner Rates",
        color_continuous_scale="Blues",
        labels={"high_earner_rate": "High-Earner Rate"},
    )
    fig_map.update_layout(
        template="plotly_white",
        margin=dict(l=0, r=0, t=40, b=0),
        geo=dict(
            showframe=False, showcoastlines=True, projection_type="equirectangular"
        ),
    )

    # Top Countries Bar Chart
    top_countries = country_df.head(15).sort_values("freelancer_count", ascending=True)
    fig_top_countries = px.bar(
        top_countries,
        x="freelancer_count",
        y="country",
        orientation="h",
        title="Top 15 Countries by Freelancer Population",
        labels={"freelancer_count": "Freelancers", "country": "Country"},
        color="median_hourly_rate",
        color_continuous_scale="Viridis",
    )
    fig_top_countries.update_layout(
        template="plotly_white",
        margin=dict(l=20, r=20, t=40, b=20),
    )

    # City Table for Top Countries
    city_table_data = city_df.head(25).copy()
    city_table_data["high_earner_rate"] = city_table_data["high_earner_rate"].apply(
        lambda v: f"{v * 100:.1f}%"
    )
    city_table_data["median_earnings"] = city_table_data["median_earnings"].apply(
        lambda v: f"${v:,.0f}"
    )
    city_table_data["median_hourly_rate"] = city_table_data["median_hourly_rate"].apply(
        lambda v: f"${v:,.0f}/hr"
    )

    city_table = dash_table.DataTable(
        columns=[
            {"name": "Country", "id": "country"},
            {"name": "City", "id": "city"},
            {"name": "Freelancers", "id": "freelancer_count"},
            {"name": "High-Earner %", "id": "high_earner_rate"},
            {"name": "Median Earnings", "id": "median_earnings"},
            {"name": "Hourly Rate", "id": "median_hourly_rate"},
        ],
        data=city_table_data.to_dict("records"),
        page_size=10,
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
                        "Geographic Distribution & Regional Disparities",
                        className="fw-bold text-dark",
                    ),
                    html.P(
                        "Cross-country and metropolitan variation in freelancer density, median hourly rates, high-earner concentration, and dominant localized skillsets.",
                        className="text-muted",
                    ),
                ],
                className="mb-4",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody([dcc.Graph(figure=fig_map, responsive=True)]),
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
                                [dcc.Graph(figure=fig_top_countries, responsive=True)]
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
                                        "Metropolitan Centers Drill-Down",
                                        className="fw-bold mb-3",
                                    ),
                                    city_table,
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
