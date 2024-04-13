import pytest
from ttipabot import analyser
from pathlib import Path
import datetime

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
    assert analyser.get_csv_filepaths(folderpath) == sorted(filepaths)

def test_validate_date():
    analyser.validate_date("2023-03-20")
    with pytest.raises(Exception):
        assert analyser.validate_date("20-03-2023")

def test_latest_csvs(paths: tuple[Path, Path]):
    filepaths = paths[1]
    # Order doesn't matter
    assert sorted(analyser.get_latest_csvs(filepaths, 2)) == sorted(filepaths[-2:])

def test_latest_csvs_single(paths: tuple[Path, Path]):
    filepaths = paths[1]
    #print(filepaths)
    assert analyser.get_latest_csvs(filepaths, 1) == [filepaths[2]]

def test_select_filepaths_for_dates(paths: tuple[Path, Path]):
    filepaths = paths[1]
    # Specifying dates that both have a file
    assert analyser.select_filepaths_for_dates(filepaths, ["2023-03-20", "2023-06-25"]) == [filepaths[0], filepaths[2]]

def test_select_filepaths_for_dates_nonexistent(paths: tuple[Path, Path]):
    filepaths = paths[1]
    # Trying to specify a date that doesn't have a file
    with pytest.raises(ValueError,  match="No file exists for 2099-06-25"):
        analyser.select_filepaths_for_dates(filepaths, ["2023-03-20", "2099-06-25"]) == [filepaths[0], None]

def test_select_filepaths_for_dates_malformed(paths: tuple[Path, Path]):
    filepaths = paths[1]
    # Entering a string that is not a date
    with pytest.raises(ValueError, match="Incorrect date format, should be YYYY-MM-DD"):
        analyser.select_filepaths_for_dates(filepaths, ["garbage", "garbage"])

def test_check_already_scraped(paths: tuple[Path, Path]):
    folderpath = paths[0]
    assert not analyser.check_already_scraped(folderpath)
    # Add a file with today's date
    datePath = folderpath / f"{datetime.date.today()}.csv"
    datePath.touch()
    assert analyser.check_already_scraped(folderpath)

