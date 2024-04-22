from script_maker2000.files import (
    read_config,
    create_working_dir_structure,
    collect_input_files,
    read_mol_input_json,
)


import logging
import pathlib
import pytest
import tarfile

script_maker_log = logging.getLogger("Script_maker_log")
script_maker_error = logging.getLogger("Script_maker_error")


def test_read_config(test_setup_work_dir):

    config = read_config(test_setup_work_dir / "example_config.json")

    assert (test_setup_work_dir / config["main_config"]["output_dir"]).exists()

    assert config["main_config"]["max_n_jobs"] == 20

    with pytest.raises(FileNotFoundError):
        config = read_config(test_setup_work_dir / "example_config3.json")


def test_create_working_dir_structure(test_setup_work_dir):
    main_config = read_config(test_setup_work_dir / "example_config.json")

    # input_location = temp_work_dir / "example_molecules.csv"
    create_working_dir_structure(main_config)

    # check that log files, settings, inputs and dirs are at the correct level
    output_path = pathlib.Path(main_config["main_config"]["output_dir"])

    # expecting 5 files at the top level
    # finished, start_input_files, working, example_config.json, example_molecules.json

    assert len(list(output_path.glob("*"))) == 5
    # check that sub dirs are present
    assert len(list(output_path.glob("*/*"))) == 15
    assert len(list(output_path.glob("*/*/*"))) == 10

    # reset input filenames
    for file in pathlib.Path(test_setup_work_dir / "example_xyz").glob("*.xyz"):
        file.rename(file.parent / file.name.replace("START___", "START_"))

    with pytest.raises(
        FileExistsError, match=r"The directory .* already has subfolders setup\. .*"
    ):
        main_config = read_config(test_setup_work_dir / "example_config4.json")
        create_working_dir_structure(main_config)

    for file in pathlib.Path(test_setup_work_dir / "example_xyz").glob("*.xyz"):
        file.rename(file.parent / file.name.replace("START___", "START_"))

    main_config = read_config(test_setup_work_dir / "example_config5.json")
    output_path = pathlib.Path(main_config["main_config"]["output_dir"])

    create_working_dir_structure(main_config)

    # expecting 5 files at the top level
    # finished, start_input_files, working, example_config.json, example_molecules.json
    assert len(list(output_path.glob("*"))) == 5
    # check that two new sub dirs are present
    assert len(list(output_path.glob("*/*"))) == 15
    assert len(list(output_path.glob("*/*/*"))) == 9

    with pytest.raises(KeyError):
        read_config(test_setup_work_dir / "example_config6.json")


def test_collect_input_files(clean_tmp_dir):

    tar_path = collect_input_files(
        clean_tmp_dir / "example_config.json", clean_tmp_dir / "example_prep"
    )
    extract_path = clean_tmp_dir / "example_prep" / "extracted_test"
    with tarfile.open(tar_path, "r:gz") as tar:
        tar.extractall(path=extract_path, filter="fully_trusted")

    assert len(list(extract_path.glob("*"))) == 3
    assert len(list(extract_path.glob("*/*"))) == 11


def test_read_mol_input_json(clean_tmp_dir):

    import pandas as pd

    print(clean_tmp_dir)
    json_path = clean_tmp_dir / "example_xyz" / "example_molecules.json"
    example_mol_dict = read_mol_input_json(json_path)

    df = pd.DataFrame(example_mol_dict)
    print(df)
