import logging
from pathlib import Path
from os.path import dirname, realpath

import pandas as pd


# Custom modules
from ttipabot import scraper
from ttipabot import analyser
from ttipabot import chanter

logger = logging.getLogger(__name__)
logging.basicConfig(filename='ttipabot.log', encoding='utf-8', format='%(asctime)s %(message)s', level=logging.DEBUG)

#TODO Refactor directory lookup to avoid using global
CSV_FOLDER = Path(__file__).parents[0] / "scrapes"
print(CSV_FOLDER)

def scrape_register() -> None:
    """Scrapes the register, parses all the data, and writes it to a csv file."""
    if analyser.check_already_scraped(CSV_FOLDER):
        print("Already performed a scrape today.")
        return
    results = scraper.get_full_register()
    data = scraper.parse_register(results)
    scraper.write_to_csv(data, CSV_FOLDER)


def get_latest_dates(num: int) -> list[str]:
    """Gets the <num> latest dates among all the existing csv filepaths."""
    csvFilepaths = analyser.get_csv_filepaths(CSV_FOLDER)
    latestCsvFilepaths = analyser.get_latest_csvs(csvFilepaths, num)
    dates = [filepath.stem for filepath in latestCsvFilepaths]
    # If there's not enough dates available, fill the rest of the list with blanks
    if len(dates) < num:
        diff = num-len(dates)
        dates.extend(['']*diff)
    
    return dates

def get_latest_date() -> str:
    """Gets the latest date among all the existing csv filepaths."""
    return get_latest_dates(num=1)[0]

def count_dates() -> int:
    return len(analyser.get_csv_filepaths(CSV_FOLDER))

def rank_names(date: str, num: int, chant: bool) -> None:
    """Prints the <num> longest names on the register as of <date>."""
    csvFilepaths = analyser.get_csv_filepaths(CSV_FOLDER)
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
    
    csvFilepaths = analyser.get_csv_filepaths(CSV_FOLDER)
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
    print(f"Available dates ({num}):")
    #TODO prettify layout with columns or grid for large numbers
    for date in get_latest_dates(num):
        print(date)

def rank_firms(date: str, num: int, pat: bool, tm: bool, raw: bool) -> None:
    """Prints the <num> biggest firms (by attorney count) on the register as of <date>."""
    csvFilepaths = analyser.get_csv_filepaths(CSV_FOLDER)
    csv = analyser.select_filepaths_for_dates(csvFilepaths, [date])[0]
    df = analyser.csv_to_df(csv)

    df = analyser.filter_attorneys(df, pat, tm)
    df_firms = analyser.firm_rank_df(df, num, raw)

    print(f"\nThe biggest {num} firms by attorney count as of {date} are:\n{df_firms[['Firm', 'Attorneys']].to_markdown()}")