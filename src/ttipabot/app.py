import logging
from pathlib import Path

import pandas as pd


# Custom modules
from ttipabot import scraper
from ttipabot import analyser
from ttipabot import chanter

logger = logging.getLogger(__name__)
logging.basicConfig(filename='ttipabot.log', encoding='utf-8', format='%(asctime)s %(message)s', level=logging.DEBUG)

CSV_FOLDER = Path.cwd() / "TTIPAB register saves"

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
    latestCsvFilepaths = analyser.get_latest_csvs(analyser.get_csv_filepaths(CSV_FOLDER), num)
    dates = [filepath.stem for filepath in latestCsvFilepaths]
    return dates

def rank_names(date: str, num: int, chant: bool) -> None:
    """Prints the <num> longest names on the register as of <date>."""
    csvFilepaths = analyser.get_csv_filepaths(CSV_FOLDER)
    csv = analyser.select_filepaths_for_dates(csvFilepaths, [date])[0]
    df_names = analyser.csv_to_ranked_df(csv, num)

    print(f"\nThe top {num} names by length are:\n{df_names[['Name', 'Length']].to_markdown()}")

    # Play a Sardaukar chant if there are any new attorneys. Otherwise shorter chant with a random quote.
    if not chant: return 
    lines = analyser.attorneys_df_to_lines(df_names)
    chanter.perform_chant(lines)


def compare_data(dates: tuple[str, str], chant: bool) -> None:
    date1, date2 = dates
    dates = sorted([date1, date2])
    
    csvFilepaths = analyser.get_csv_filepaths(CSV_FOLDER)
    (csv1, csv2) = analyser.select_filepaths_for_dates(csvFilepaths, dates)
    logger.debug(f"Comparing dates {dates[0]} and {dates[1]}")

    try:
        (newAttorneys_df, firmChanges_df) = analyser.compare_csvs(csv1, csv2)

        if not newAttorneys_df.empty: 
            print(f"\nCongratulations to the following newly registered IP attorneys:\n{newAttorneys_df.to_markdown()}\n")
        if not firmChanges_df.empty: 
            print(f"The following attorneys have recently changed firm:\n{firmChanges_df.to_markdown()}\n")

    except Exception as ex:
        logger.error(f"Error analysing data, possibly anomaly in register.", exc_info= ex)
        # Create empty data frame so that the random chant can proceed
        newAttorneys_df = pd.DataFrame([])

    # Play a Sardaukar chant if there are any new attorneys.
    if not chant: return 

    # Get a list of all the new patent attorneys by eliminating solely TM registered (will still capture blanks, in case data missing)
    patentAttorneys_df = analyser.remove_TM_attorneys(newAttorneys_df)
    lines = analyser.attorneys_df_to_lines(patentAttorneys_df)
    chanter.perform_chant(lines)

        