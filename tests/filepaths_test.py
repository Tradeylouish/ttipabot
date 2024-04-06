import pytest
import ttipabot

@pytest.fixture(scope="session")
def paths(tmp_path_factory):
    """Mock a directory of csv files"""
    d = tmp_path_factory.mktemp('saves')
    filepaths = [d / '2023-03-20.csv', d / '2023-06-10.csv', d / '2023-06-25.csv']
    for filepath in filepaths:
        filepath.touch()
    # Add a non-csv file to folder
    txtPath = d / 'garbage.txt'
    txtPath.write_text('')
    return (d, filepaths)

def test_get_csv_filepaths(paths):
    (folderpath, filepaths) = paths
    # Order doesn't matter
    assert ttipabot.get_csv_filepaths(folderpath) == sorted(filepaths)

def test_latest_csvs(paths):
    filepaths = paths[1]
    assert ttipabot.get_latest_csvs(filepaths, 2) == [filepaths[2], filepaths[1]]

def test_latest_csvs_single(paths):
    filepaths = paths[1]
    assert ttipabot.get_latest_csvs(filepaths, 1) == [filepaths[2]]

def test_specified_csvs(paths):
    filepaths = paths[1]
    # Specifying dates that both have a file
    assert ttipabot.get_specified_csvs(filepaths, ["2023-03-20", "2023-06-25"]) == [filepaths[0], filepaths[2]]

def test_specified_csvs_nonexistent(paths):
    filepaths = paths[1]
    # Trying to specify a date that doesn't have a file
    assert ttipabot.get_specified_csvs(filepaths, ["2023-03-20", "2099-06-25"]) == [filepaths[0], None]

def test_specified_csvs_malformed(paths):
    filepaths = paths[1]
    # Malformed strings - should raise exception
    with pytest.raises(Exception):
        ttipabot.get_specified_csvs(filepaths, ["garbage", "garbage"])