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
    """Gets <num> dates from among those with available scrapes, and pads with blanks up to a date pair."""
    dates = scraper.get_dates(num, oldest, changesOnly)
    # Blanks to allow cli default calls without errors when there's no scrapes
    if len(dates) < 2 and num <= 2:
        diff = num-len(dates)
        dates.extend(['']*diff)
    return dates

def get_latest_date() -> str:
    """Gets the latest date among all those available."""
    return get_dates(num=1)[0]

def count_dates(changes_only=False) -> int:
    """Returns the total number of dates available."""
    return scraper.count_dates(changes_only=False)

def compare_data(dates: tuple[str, str], pat: bool, tm: bool, mode: str, json: bool = False) -> str:
    """Compares scraped data between two different dates according to a specified mode from among the following:
    registrations
    movements
    lapses"""
    dates = sorted(list(dates))
    csv1, csv2 = scraper.dates_to_filepaths(dates)
    logger.debug(f"Comparing dates {dates[0]} and {dates[1]}")
    comparison_df = analyser.compare_data(csv1, csv2, pat, tm, mode)
    
    if json: 
        return comparison_df.to_json(orient = "records")
    # If there's no results, output empty string instead of the headers
    if comparison_df.empty: 
        return ""
    return comparison_df.to_markdown()
    

def rank_data(date: str, num: int, pat: bool, tm: bool, mode: str, json: bool=False, raw: bool = False) -> str:
    csv = scraper.dates_to_filepaths([date])[0]
    ranking_df = analyser.rank_data(csv, num, pat, tm, mode, raw)
    if json:
        return ranking_df.to_json(orient = "records")
    return ranking_df.to_markdown()

def cleanup() -> int:
    """Cleans up duplicate csv files by mapping dupes to earlier dates, and returns the number of csvs cleaned."""
    return scraper.clean_csvs(recentOnly=False)
    