from dash import Dash, html
import dash_bootstrap_components as dbc
from script_maker2000.dash_ui.config_maker_ui import (
    create_config_manager_layout,
    add_callbacks,
)
from script_maker2000.dash_ui.remote_explorer import (
    create_manager_layout,
    add_callbacks_remote_explorer,
)


def create_main_app(file_path: str, remote_connection):

    app = Dash("Test", external_stylesheets=[dbc.themes.LITERA])
    config_div = create_config_manager_layout(file_path)
    remote_explorer_layout = create_manager_layout()

    tabs = dbc.Tabs(
        [
            dbc.Tab(
                tab_id="config",
                label="Config",
                children=[config_div],
                style={"padding-top": "20px"},
            ),
            dbc.Tab(
                tab_id="managment",
                label="Managment",
                children=[remote_explorer_layout],
                style={"padding-top": "20px"},
            ),
        ],
        active_tab="config",
    )

    app.layout = html.Div(id="main_div", children=[tabs], style={"padding": "20px"})
    app = add_callbacks(app)
    app = add_callbacks_remote_explorer(app, remote_connection)
    return app
