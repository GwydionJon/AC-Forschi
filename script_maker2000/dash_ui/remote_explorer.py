import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State
import dash_treeview_antd as dta
from pathlib import Path
from script_maker2000.dash_ui.config_maker_ui import create_new_intput
from script_maker2000.dash_ui.remote_explorer_calls import (
    convert_paths_to_dict,
    print_selected_path,
    return_selected_path,
    check_local_tar_file,
    get_local_paths,
)

default_style = {"margin": "10px", "width": "100%"}


def create_manager_layout():

    remote_explorer_layout = create_remote_explorer_layout("remote")
    local_explorer_layout = create_remote_explorer_layout("local")
    submission_layout = create_job_submission_layout()

    layout = dbc.Row(
        children=[
            dbc.Col(
                children=[
                    local_explorer_layout,
                ],
                width=3,
                style={"padding-right": "10px"},
            ),
            dbc.Col(
                children=[
                    remote_explorer_layout,
                ],
                width=3,
            ),
            dbc.Col(
                children=[
                    submission_layout,
                ],
                width=3,
                style={"padding-left": "10px"},
            ),
        ]
    )

    return layout


def create_remote_explorer_layout(mode):

    if mode == "remote":
        header_text = [
            "This is the remote explorer.",
            html.Br(),
            " Select the directory where you want to start the calculation.",
        ]
        input_id = "remote_path_input"
        input_label = "Enter remote path:"
        input_value = ""
        input_placeholder = "Remote dir or path"

    if mode == "local":
        header_text = [
            "This is the local explorer.",
            html.Br(),
            "Select the local tar ball you want to submit.",
        ]
        input_id = "local_path_input"
        input_label = "Enter local path:"
        input_value = "."
        input_placeholder = "Local dir or path"

    layout = dbc.Row(
        children=[
            # explanation text for the user
            html.P(header_text, style=default_style),
            create_new_intput(input_label, input_value, input_id, input_placeholder),
            # text field to show wich path is selected
            html.P(
                id=f"{mode}_path_output",
                children="No path selected yet.",
                style={"margin": "10px", "width": "100%", "height": "50px"},
            ),
            dbc.Button(
                "Search path",
                id=f"{mode}_explorer_submit",
                style={"margin": "10px", "width": "80%", "align": "center"},
            ),
            # checkable, checked, data, expanded, id, multiple, selected
            dcc.Loading(
                children=[
                    dta.TreeView(
                        multiple=False,
                        checkable=False,
                        id=f"{mode}_tree_view",
                        data=None,
                    ),
                ]
            ),
        ],
    )

    return layout


def create_job_submission_layout():
    placeholder = "Select files to submit."

    layout = dbc.Row(
        children=[
            html.H3("Job submission", style=default_style),
            html.P(
                [
                    "To submit a job you should have collected the input files in the Config tab."
                    + " This will create a tar.gz file.",
                    html.Br(),
                    "Use the file explorer on the left to select the tar.gz of the job you want to submit.",
                    html.Br(),
                    "Use the file explorer on the right to select the parent directory for the calculation.",
                ],
                style=default_style,
            ),
            create_new_intput(
                "Select the tar file of your calculation. (See Config tab)",
                "",
                "valid_input_file",
                placeholder,
                True,
            ),
            create_new_intput(
                "Select the parent dir for your calculation. (Use / to add a new dir)",
                "",
                "valid_target_dir",
                placeholder,
                False,
            ),
            html.P(
                "If these are correct, press the submit button to start a new calculation.",
                style=default_style,
            ),
            dbc.Button(
                "Submit job", id="submit_new_job", style=default_style, disabled=True
            ),
            dbc.Textarea(
                id="job_output",
                style={"margin": "10px", "width": "100%", "height": "400px"},
                readOnly=True,
            ),
        ]
    )
    return layout


def add_callbacks_remote_explorer(app, remote_connection):

    def get_remote_paths(n_clicks, path):

        if path is None:
            path = "."

        if path[-1] != "/":
            path = path + "/"
        output = remote_connection.run(
            f"find {path} -not -path '*/\.*' -print", hide=True  # noqa
        )
        output = output.stdout.split("\n")[:-1]
        output = convert_paths_to_dict(output, mode="remote")

        cwd = remote_connection.run("pwd", hide=True).stdout.strip()

        return {"title": cwd, "key": cwd, "children": output}

    def submit_job(n_clicks, input_file, target_dir):

        print("starting job")
        if input_file is None or target_dir is None:
            return "No job submitted yet."

        # use batch to check is the target dir exists, and if not recursivly create it.
        remote_connection.run(
            f"test -d {target_dir} || mkdir -p {target_dir}",
            hide=True,
        )

        result = remote_connection.put(input_file, target_dir)

        # check if the script manager has already been installed by the user, if not do so.
        result_installed_check = remote_connection.run(
            r"command -v script_maker_cli >/dev/null 2>&1 && echo 'The orca script manager is installed.' ||"
            + " { echo >&2 'The Script maker package is not installed. Installing now:.'; "
            + "ml devel/python/3.11.4; echo 'Unsetting pip'; unset PIP_TARGET; "
            + "pip install git+https://github.com/GwydionJon/Orca_script_manager; }",
            timeout=210,
            hide=True,
        ).stdout

        output_text = f"{Path(input_file).name} uploaded to {result.remote}.\n"
        output_text += (
            f"Check if script manager is installed: \n{result_installed_check}\n\n"
        )

        # start the calculation using nohup
        result = remote_connection.run(
            f"nohup script_maker_cli start-tar --tar {Path(input_file).name} &",
            hide=True,
        )
        output_text += f"{result.stdout}\n\n"
        output_text += "Job started in background. Check the log file for progress.\n"

        return output_text

    app.callback(
        Output("job_output", "value"),
        Input("submit_new_job", "n_clicks"),
        State("valid_input_file", "value"),
        State("valid_target_dir", "value"),
        prevent_initial_call=False,
    )(submit_job)

    app.callback(
        Output("local_tree_view", "data"),
        Input("local_explorer_submit", "n_clicks"),
        State("local_path_input", "value"),
        prevent_initial_call=False,
    )(get_local_paths)

    app.callback(
        Output("remote_tree_view", "data"),
        Input("remote_explorer_submit", "n_clicks"),
        State("remote_path_input", "value"),
        prevent_initial_call=False,
    )(get_remote_paths)

    app.callback(
        Output("remote_path_output", "children"),
        Input("remote_tree_view", "selected"),
        prevent_initial_call=True,
    )(print_selected_path)

    app.callback(
        Output("local_path_output", "children"),
        Input("local_tree_view", "selected"),
        prevent_initial_call=True,
    )(print_selected_path)

    app.callback(
        Output("valid_input_file", "value"),
        Input("local_tree_view", "selected"),
        prevent_initial_call=True,
    )(return_selected_path)

    app.callback(
        Output("valid_target_dir", "value"),
        Input("remote_tree_view", "selected"),
        prevent_initial_call=True,
    )(return_selected_path)

    app.callback(
        Output("valid_input_file", "valid"),
        Output("valid_input_file", "invalid"),
        Output("submit_new_job", "disabled"),
        Input("valid_input_file", "value"),
        prevent_initial_call=True,
    )(check_local_tar_file)

    return app
