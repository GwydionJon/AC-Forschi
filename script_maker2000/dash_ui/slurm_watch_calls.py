from collections import defaultdict

# import json
from pathlib import Path

# import dash_bootstrap_components as dbc
# from dash import html
import pandas as pd

sacct_dict = Path(__file__).parent / "sacct_options.json"


def get_sacct_output(
    n_clicks, start_date, end_date, time_range, format_entries, remote_connection
):
    print("n_clicks:", n_clicks)
    print("start_date:", start_date)
    print("end_date:", end_date)
    print("time_range:", time_range)
    print("format_entries:", format_entries)

    sacct_command = "sacct -p"

    if start_date:
        sacct_command += f" -S {start_date}T{time_range[0]}:00"

    if end_date:
        if time_range[1] == 24:
            time_range[1] = "00"
            end_date = end_date[:-1] + str(int(end_date[-1]) + 1)
        sacct_command += f" -E {end_date}T{time_range[1]}:00"

    if format_entries:
        sacct_command += f" --format={','.join(format_entries)}"
    print(sacct_command)
    slurm_output = remote_connection.run(sacct_command, hide=True).stdout

    split_rows = slurm_output.split("\n")
    row_dict = defaultdict(dict)
    for i, row in enumerate(split_rows):
        if i == 0:
            column_names = row.split("|")
        else:
            row_values = row.split("|")
            if len(row_values) == 1:
                continue
            row_dict[row_values[0]] = {
                column_names[i]: row_values[i] for i in range(1, len(column_names))
            }

    df = pd.DataFrame(row_dict).T
    df.reset_index(inplace=True)
    columns = [{"name": i, "id": i} for i in df.columns[:-1]]

    print(df)
    return df.to_dict("records"), columns