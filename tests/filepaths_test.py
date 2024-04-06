import pytest
import ttipabot
from pathlib import Path

@pytest.fixture(scope="session")
def paths(tmp_path_factory) -> tuple[Path, Path]:
    """Mock a directory of csv files"""
    d = tmp_path_factory.mktemp('saves')
    filepaths = [d / '2023-03-20.csv', d / '2023-06-10.csv', d / '2023-06-25.csv']
    for filepath in filepaths:
        filepath.touch()
    # Add a non-csv file to folder
    txtPath = d / 'garbage.txt'
    txtPath.write_text('')
    return (d, filepaths)

def test_get_csv_filepaths(paths: tuple[Path, Path]):
    (folderpath, filepaths) = paths
    # Should be time-ordered
    assert ttipabot.get_csv_filepaths(folderpath) == sorted(filepaths)

def test_latest_csvs(paths: tuple[Path, Path]):
    filepaths = paths[1]
    assert ttipabot.get_latest_csvs(filepaths, 2) == [filepaths[2], filepaths[1]]

def test_latest_csvs_single(paths: tuple[Path, Path]):
    filepaths = paths[1]
    assert ttipabot.get_latest_csvs(filepaths, 1) == [filepaths[2]]

def test_select_filepaths_for_dates(paths: tuple[Path, Path]):
    filepaths = paths[1]
    # Specifying dates that both have a file
    assert ttipabot.select_filepaths_for_dates(filepaths, ["2023-03-20", "2023-06-25"]) == [filepaths[0], filepaths[2]]

def test_select_filepaths_for_dates_nonexistent(paths: tuple[Path, Path]):
    filepaths = paths[1]
    # Trying to specify a date that doesn't have a file
    with pytest.raises(ValueError,  match="No file exists for 2099-06-25"):
        ttipabot.select_filepaths_for_dates(filepaths, ["2023-03-20", "2099-06-25"]) == [filepaths[0], None]

def test_select_filepaths_for_dates_malformed(paths: tuple[Path, Path]):
    filepaths = paths[1]
    # Entering a string that is not a date
    with pytest.raises(ValueError, match="Incorrect date format, should be YYYY-MM-DD"):
        ttipabot.select_filepaths_for_dates(filepaths, ["garbage", "garbage"])