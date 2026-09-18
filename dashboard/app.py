"""Interactive Multi-page Dash Application for Skill Bundles and Freelancer Earnings Analysis."""

import dash
import dash_bootstrap_components as dbc
from dash import Dash, html

app = Dash(
    __name__,
    use_pages=True,
    pages_folder="pages",
    external_stylesheets=[dbc.themes.FLATLY, dbc.icons.FONT_AWESOME],
    suppress_callback_exceptions=True,
    title="Skill Bundles & Earnings Analytics",
)

navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(
            dbc.NavLink(
                [html.I(className="fa-solid fa-chart-pie me-2"), "Overview"], href="/"
            )
        ),
        dbc.NavItem(
            dbc.NavLink(
                [html.I(className="fa-solid fa-cubes me-2"), "Skill Bundles"],
                href="/skill-bundles",
            )
        ),
        dbc.NavItem(
            dbc.NavLink(
                [html.I(className="fa-solid fa-diagram-project me-2"), "Skill Network"],
                href="/skill-network",
            )
        ),
        dbc.NavItem(
            dbc.NavLink(
                [html.I(className="fa-solid fa-language me-2"), "Profile Language"],
                href="/profile-language",
            )
        ),
        dbc.NavItem(
            dbc.NavLink(
                [html.I(className="fa-solid fa-earth-americas me-2"), "Geography"],
                href="/geography",
            )
        ),
    ],
    brand=html.Span(
        [
            html.I(className="fa-solid fa-briefcase me-2 text-primary"),
            html.Strong("Skill Bundles & Freelancer Earnings"),
        ]
    ),
    brand_href="/",
    color="light",
    dark=False,
    className="mb-4 shadow-sm border-bottom",
    fluid=True,
)

footer = html.Footer(
    dbc.Container(
        [
            html.Hr(className="my-4"),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.P(
                                [
                                    "Skill Bundles and Freelancer Earnings Analytical Harness | Built with ",
                                    html.Strong(
                                        "DuckDB, Scikit-learn, NetworkX & Plotly Dash"
                                    ),
                                ],
                                className="text-muted mb-0 small",
                            )
                        ],
                        md=8,
                    ),
                    dbc.Col(
                        [
                            html.P(
                                "Optimized for high scalability (3M+ records under 16GB RAM constraints)",
                                className="text-muted text-md-end mb-0 small",
                            )
                        ],
                        md=4,
                    ),
                ],
                className="align-items-center mb-3",
            ),
        ],
        fluid=True,
    )
)

app.layout = html.Div(
    [
        navbar,
        dbc.Container(dash.page_container, fluid=True, className="px-4 pb-4"),
        footer,
    ],
    className="min-vh-100 d-flex flex-column justify-content-between bg-light",
)

server = app.server

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050, debug=False)
