import pytest
from ttipabot import scraper
from pathlib import Path
import datetime

@pytest.fixture(scope="session")
def paths(tmp_path_factory) -> tuple[Path, Path]:
    """Mock a directory of csv files"""
    d = tmp_path_factory.mktemp('saves')
    filepaths = [d / '2023-03-20.csv', d / '2023-06-10.csv', d / '2023-06-25.csv']
    for filepath in filepaths:
        filepath.touch()
    # Add a non-csv file to directory
    txtPath = d / 'date_table.txt'
    txtPath.write_text('')
    return (d, filepaths)

def test_get_csv_filepaths(paths: tuple[Path, Path]):
    (dirPath, filepaths) = paths
    # Should be time-ordered
    assert scraper.get_csv_filepaths(dirPath) == sorted(filepaths)

def test_validate_date():
    scraper.validate_date("2023-03-20")
    with pytest.raises(Exception):
        assert scraper.validate_date("20-03-2023")

def test_select_filepaths_for_dates(paths: tuple[Path, Path]):
    dirPath, filepaths = paths
    # Specifying dates that both have a file
    assert scraper.select_filepaths_for_dates(dirPath, ["2023-03-20", "2023-06-25"]) == [filepaths[0], filepaths[2]]

def test_select_filepaths_for_dates_nonexistent(paths: tuple[Path, Path]):
    dirPath, filepaths = paths
    # Trying to specify a date that doesn't have a file
    with pytest.raises(ValueError,  match="No file exists for 2099-06-25"):
        scraper.select_filepaths_for_dates(dirPath, ["2023-03-20", "2099-06-25"]) == [filepaths[0], None]

def test_select_filepaths_for_dates_malformed(paths: tuple[Path, Path]):
    dirPath = paths[0]
    # Entering a string that is not a date
    with pytest.raises(ValueError, match="Missing or incorrectly formatted date, should be YYYY-MM-DD"):
        scraper.select_filepaths_for_dates(dirPath, ["garbage", "garbage"])

def test_clean_csvs(paths: tuple[Path, Path]):
    dirPath, filepaths = paths
    scraper.clean_csvs(recentOnly=False, dirPath=dirPath)
    assert scraper.get_csv_filepaths(dirPath) == [filepaths[0]]
    assert scraper.read_date_table(dirPath) == {"2023-06-10" : "2023-03-20", "2023-06-25" : "2023-03-20"}

def test_check_already_scraped(paths: tuple[Path, Path]):
    dirPath = paths[0]
    assert not scraper.check_already_scraped(dirPath)
    # Add a file with today's date
    datePath = dirPath / f"{datetime.date.today()}.csv"
    datePath.touch()
    assert scraper.check_already_scraped(dirPath)
    
def test_check_already_scraped_table(paths: tuple[Path, Path]):
    dirPath = paths[0]
    # Add a line to the date table
    scraper.append_to_date_table(dirPath, [datetime.date.today(), "2024-10-26"])
    assert scraper.check_already_scraped(dirPath)
    
