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
    results = scraper.get_full_register()
    data = scraper.parse_register(results)
    scraper.write_to_csv(data, CSV_FOLDER)


def get_latest_dates(num: int) -> list[str]:
    """Gets the <num> latest dates among all the existing csv filepaths."""
    latestCsvFilepaths = analyser.get_latest_csvs(analyser.get_csv_filepaths(CSV_FOLDER), num)
    dates = [filepath.stem for filepath in latestCsvFilepaths]
    return dates

def rank_names(date: str, num: int) -> None:
    """Prints the <num> longest names on the register as of <date>."""
    csvFilepaths = analyser.get_csv_filepaths(CSV_FOLDER)
    csv = analyser.select_filepaths_for_dates(csvFilepaths, [date])[0]

    df = pd.read_csv(csv, dtype='string')

    # Replace missing values with empty strings for comparison purposes
    df.fillna('')

    # Sort names and reindex to show ranking
    df['Length'] = df['Name'].apply(lambda col: len(col))
    df = df.sort_values(by='Length', ascending=False)
    df.reset_index(inplace=True)
    df.index += 1
    print(f"\nThe top {num} names by length are:\n{df[['Name', 'Length']].head(num).to_markdown()}")


def compare_data(dates: tuple[str, str], chant: bool) -> None:
    date1, date2 = dates
    dates = sorted([date1, date2])
    
    csvFilepaths = analyser.get_csv_filepaths(CSV_FOLDER)

    (csv1, csv2) = analyser.select_filepaths_for_dates(csvFilepaths, dates)

    logger.debug(f"Comparing dates {dates[0]} and {dates[1]}")

    try:
        (newAttorneys, firmChanges) = analyser.compare_csvs(csv1, csv2)

        if not newAttorneys.empty: 
            print(f"\nCongratulations to the following newly registered IP attorneys:\n{newAttorneys.to_markdown()}\n")
        if not firmChanges.empty: 
            print(f"The following attorneys have recently changed firm:\n{firmChanges.to_markdown()}\n")

    except Exception as ex:
        logger.error(f"Error analysing data, possibly anomaly in register.", exc_info= ex)
        # Create empty data frame so that the random chant can proceed
        newAttorneys = pd.DataFrame([])

    # Play a Sardaukar chant if there are any new attorneys. Otherwise shorter chant with a random quote.
    if not chant: return 

    # Get a list of all the new patent attorneys by eliminating solely TM registered (will still capture blanks, in case data missing)
    patentAttorneys = [newAttorney for newAttorney in newAttorneys.itertuples() if newAttorney._3 != 'Trade marks']

    sound_file, text = chanter.choose_line(patentAttorneys)
    chanter.perform_chant(sound_file, text)

        