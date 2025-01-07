import logging
from pathlib import Path

import pandas as pd

# Custom modules
from ttipabot import scraper, analyser

logger = logging.getLogger(__name__)
logging.basicConfig(filename='ttipabot.log', encoding='utf-8', format='%(asctime)s %(message)s', level=logging.DEBUG)

def scrape_register() -> bool:
    """Scrapes the register, parses all the data, and writes it to a csv file."""
    return scraper.scrape_register()

def get_dates(num: int, oldest: bool = False, changesOnly: bool = False) -> list[str]:
    """Gets <num> dates from the newest or oldest existing csv filepaths."""
    dates = scraper.get_dates(num, oldest, changesOnly)
     # Blanks to allow cli default calls without errors when no files
    if len(dates) < 2 and num <= 2:
        diff = num-len(dates)
        dates.extend(['']*diff)
    return dates

def get_latest_date() -> str:
    """Gets the latest date among all those available."""
    return get_dates(num=1)[0]

def count_dates() -> int:
    """Returns the total number of dates available."""
    return scraper.count_dates()

def rank_names(date: str, num: int, markdown: bool) -> str:
    """Prints the <num> longest names on the register as of <date>."""
    csv = scraper.dates_to_filepaths([date])[0]
    df = analyser.csv_to_df(csv)
    df_names = analyser.name_rank_df(df, num)

    if markdown:
        return df_names[['Name', 'Length']].to_markdown()
    # Raw list of names
    return analyser.attorneys_df_to_lines(df_names)

def compare_registrations(dates: tuple[str, str], markdown: bool, pat: bool, tm: bool):
    dates = sorted(list(dates))
    diffs_df = compare_data(dates, pat, tm)
    newAttorneys_df = analyser.get_new_attorneys_df(diffs_df)
    
    # Raw list of names
    if not markdown: 
        return analyser.attorneys_df_to_lines(newAttorneys_df)
    
    if not newAttorneys_df.empty: 
        return newAttorneys_df.to_markdown()
    return ""

def compare_movements(dates: tuple[str, str], pat: bool, tm: bool):
    dates = sorted(list(dates))
    diffs_df = compare_data(dates, pat, tm)
    firmChanges_df = analyser.get_firmChanges_df(diffs_df)
    if not firmChanges_df.empty: 
        return firmChanges_df.to_markdown()
    return ""

def compare_data(dates: list[str, str], pat: bool, tm: bool) -> str:    
    csv1, csv2 = scraper.dates_to_filepaths(dates)
    df1, df2 = analyser.csvs_to_dfs([csv1, csv2])

    # Filter out attorneys not of interest before performing comparisons
    df1 = analyser.filter_attorneys(df1, pat, tm)
    df2 = analyser.filter_attorneys(df2, pat, tm)

    logger.debug(f"Comparing dates {dates[0]} and {dates[1]}")

    try:
        diffs_df = analyser.get_diffs_df(df1, df2)

    except Exception as ex:
        logger.error(f"Error comparing data, possibly anomaly in register.", exc_info= ex)
        # Create empty data frame to stand in
        diffs_df = pd.DataFrame([])
    return diffs_df

def describe_attorney_filter(pat, tm):
    attorney_type = "IP"
    if pat and tm:
        attorney_type = "dual-registered"
    elif pat:
        attorney_type = "patent"
    elif tm:
        attorney_type = "trade mark"
    return attorney_type

def rank_firms(date: str, num: int, pat: bool, tm: bool, raw: bool) -> str:
    """Prints the <num> biggest firms (by attorney count) on the register as of <date>."""
    csv = scraper.dates_to_filepaths([date])[0]
    df = analyser.csv_to_df(csv)

    df = analyser.filter_attorneys(df, pat, tm)
    df_firms = analyser.firm_rank_df(df, num, raw)

    return df_firms[['Firm', 'Attorneys']].to_markdown()

def cleanup() -> int:
    """Cleans up duplicate csv files by mapping dupes to earlier dates, and returns the number of csvs cleaned."""
    return scraper.clean_csvs(recentOnly=False)
    