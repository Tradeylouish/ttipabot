import logging
from pathlib import Path
import os

import pandas as pd


# Custom modules
from ttipabot import scraper
from ttipabot import analyser
from ttipabot import chanter

logger = logging.getLogger(__name__)
logging.basicConfig(filename='ttipabot.log', encoding='utf-8', format='%(asctime)s %(message)s', level=logging.DEBUG)

#TODO Refactor directory lookup to avoid globals
CSV_FOLDER_NAME = "TTIPA register saves"
ROOT_FOLDER_NAME = "TTIPABot"

def find_path_to_folder(folderName: str) -> Path:
    cwd_path = Path.cwd()
    # If already in the right directory
    if folderName == cwd_path.stem:
        return cwd_path
    
    # If in a subdirectory
    if folderName in str(cwd_path):
        for parent in cwd_path.parents:
            if folderName == parent.stem:
                return parent
    
    # Recursively search for the right folder
    for path in sorted(cwd_path.rglob('*')):
            if folderName in str(path):
                return path
    
    raise Exception(f"Couldn't find the root folder {folderName}")

rootFolderPath= find_path_to_folder(ROOT_FOLDER_NAME)
csvFolderPath = rootFolderPath / CSV_FOLDER_NAME

def scrape_register() -> None:
    """Scrapes the register, parses all the data, and writes it to a csv file."""
    if analyser.check_already_scraped(csvFolderPath):
        print("Already performed a scrape today.")
        return
    results = scraper.get_full_register()
    data = scraper.parse_register(results)
    scraper.write_to_csv(data, csvFolderPath)


def get_latest_dates(num: int) -> list[str]:
    """Gets the <num> latest dates among all the existing csv filepaths."""
    csvFilepaths = analyser.get_csv_filepaths(csvFolderPath)
    latestCsvFilepaths = analyser.get_latest_csvs(csvFilepaths, num)
    dates = [filepath.stem for filepath in latestCsvFilepaths]
    return dates

def rank_names(date: str, num: int, chant: bool) -> None:
    """Prints the <num> longest names on the register as of <date>."""
    csvFilepaths = analyser.get_csv_filepaths(csvFolderPath)
    csv = analyser.select_filepaths_for_dates(csvFilepaths, [date])[0]
    df = analyser.csv_to_df(csv)
    df_names = analyser.name_rank_df(df, num)

    print(f"\nThe top {num} names by length as of {date} are:\n{df_names[['Name', 'Length']].to_markdown()}")

    # Play a Sardaukar chant if there are any new attorneys. Otherwise shorter chant with a random quote.
    if not chant: return 
    lines = analyser.attorneys_df_to_lines(df_names)
    chanter.perform_chant(lines)


def compare_data(dates: tuple[str, str], chant: bool) -> None:
    
    date1, date2 = dates
    dates = sorted([date1, date2])
    
    csvFilepaths = analyser.get_csv_filepaths(csvFolderPath)
    csv1, csv2 = analyser.select_filepaths_for_dates(csvFilepaths, dates)
    df1, df2 = analyser.csvs_to_dfs([csv1, csv2])

    logger.debug(f"Comparing dates {dates[0]} and {dates[1]}")

    try:
        (newAttorneys_df, firmChanges_df) = analyser.compare_dfs(df1, df2)

        if not newAttorneys_df.empty: 
            print(f"\nCongratulations to the new IP attorneys registered between {date1} and {date2}:\n{newAttorneys_df.to_markdown()}\n")
        if not firmChanges_df.empty: 
            print(f"The following attorneys changed firms between {date1} and {date2}:\n{firmChanges_df.to_markdown()}\n")

    except Exception as ex:
        logger.error(f"Error analysing data, possibly anomaly in register.", exc_info= ex)
        # Create empty data frame so that the random chant can proceed
        newAttorneys_df = pd.DataFrame([])

    # Play a Sardaukar chant if there are any new attorneys.
    if not chant: return 

    # Get a list of all the new patent attorneys by eliminating solely TM registered (will still capture blanks, in case data missing)
    patentAttorneys_df = analyser.remove_tm_attorneys(newAttorneys_df)
    lines = analyser.attorneys_df_to_lines(patentAttorneys_df)
    chanter.perform_chant(lines)

def print_dates(num: int) -> None:
    """Print <num> latest dates available."""
    print("Available dates:")
    for date in get_latest_dates(num):
        print(date)