import pytest
import ttipabot

def test_get_csv_filepaths(tmp_path):

    d = tmp_path / "saves"
    d.mkdir()

    paths = [d / '2023-03-20.csv', d / '2023-06-10.csv', d / '2023-06-25.csv']

    for path in paths:
        path.touch()

    assert ttipabot.getCsvFilepaths(d) == paths

    # When a non-csv file is in folder
    txtPath = d / 'garbage.txt'
    txtPath.write_text('')

    assert ttipabot.getCsvFilepaths(d) == paths

def test_latest_csvs(tmp_path):

    d = tmp_path / "saves"
    d.mkdir()

    path1 = d / '2023-03-20.csv'
    path2 = d / '2023-06-10.csv'
    path3 = d / '2023-06-25.csv'

    paths = [path1, path2 , path3]

    for path in paths:
        path.touch()

    assert ttipabot.getLatestCsvs(paths) == (path2, path3)

    # When the csvs aren't time-ordered
    paths.reverse()
    assert ttipabot.getLatestCsvs(paths) == (path2, path3)

def test_specified_csvs(tmp_path):
    d = tmp_path / "saves"
    d.mkdir()

    path1 = d / '2023-03-20.csv'
    path2 = d / '2023-06-10.csv'
    path3 = d / '2023-06-25.csv'

    paths = [path1, path2 , path3]

    for path in paths:
        path.touch()

    assert ttipabot.getSpecifiedCsvs(paths, "2023-03-20", "2023-06-25") == (path1, path3)
    # Trying to specify a date that doesn't have a file
    assert ttipabot.getSpecifiedCsvs(paths, "2023-03-20", "2099-06-25") == (path1, None)
    # Malformed strings - should raise exception
    with pytest.raises(Exception):
        ttipabot.getSpecifiedCsvs(paths, "garbage", "garbage")