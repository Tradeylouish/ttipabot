import datetime
import csv
from pathlib import Path
import logging
from filecmp import cmp
import os

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

#TODO Refactor directory lookup to avoid using global
CSV_FOLDER = Path(__file__).parents[0] / "scrapes"

def scrape_register() -> bool:
    clean_csvs(CSV_FOLDER, recentOnly=False)
    if check_already_scraped(CSV_FOLDER): return False
    results = get_full_register()
    data = parse_register(results)
    write_to_csv(data)
    # Avoid keeping sequences of multiple identical csvs, but record them in a table
    
    return True

def ttipab_request(count: int):
    """Makes a GET request to the TTIPA register asking for <count> results."""
    # Public API endpoint as determined by Inspect Element > Network > Requests on Google Chrome
    urlBase = "https://www.ttipattorney.gov.au//sxa/search/results/"
    urlOptions1 = "?s={21522AF6-8499-4C63-8CFA-02E2B97737BE}&itemid={8B94FE47-304A-4629-AD46-DD208EEF71AA}&sig=als&e=0&p="
    urlOptions2 = "&v=%7B2FCA44D4-EE00-43EC-BBBF-858C31387413%7D"
    url =  f"{urlBase}{urlOptions1}{count}{urlOptions2}"
    return requests.get(url, stream=True)

def get_full_register() -> list[BeautifulSoup]:
    """Scrapes the register, cleans the HTML, and returns a list of Soup objects representing attorneys."""
    
    try:
        #Do an intial ping of the register to determine the total number of results to be requested
        initialResponse = ttipab_request(1)
        #Convert JSON response to dict and extract count
        resultsCount = initialResponse.json().get("Count")
        #Request the full contents of the register
        rawHTML = ttipab_request(resultsCount).text
        logger.debug(f"Successfully scraped {resultsCount} results from the register.")
    except Exception as ex:
        logger.error("Failed to scrape register, could be a server-side problem.", exc_info= ex)
        raise ex

    # Get rid of control characters
    rawHTML = rawHTML.replace("\\r", "")
    rawHTML = rawHTML.replace("\\n", "")
    rawHTML = rawHTML.replace("\\", "")

    # Parse and extract all the data
    soup = BeautifulSoup(rawHTML, 'lxml')

    attorneys = soup.find_all(class_="list-item attorney")

    return attorneys

def get_contact_data(result: BeautifulSoup, searchString: str) -> str:
    """Searches for a piece of data in the attorney HTML and returns its value."""
    tag = result.find("span", string=searchString)
    if tag is None:
        return ""
    
    #Data is always in (non-whitespace) descendant string(s) of the tag that follows
    #Could be two strings for dual registrations, so comma join
    return ", ".join(tag.find_next_sibling().stripped_strings) 

def get_attorney_data(attorney: BeautifulSoup) -> list[str]:
    """Returns a list of the data entries for one attorney."""
    fields = [" Attorney ", " Phone ", " Email ", " Firm ", " Address ", " Registered as"]
    return [get_contact_data(attorney, field) for field in fields]

def parse_register(attorneys: list[BeautifulSoup]) -> list[list[str]]:
    """Returns a nested list of all the data for all attorneys (skipping any blank entries)."""
    data = [get_attorney_data(attorney) for attorney in attorneys 
            if get_contact_data(attorney, " Attorney ") != ""]
    return data

def write_to_csv(data: list[list[str]]) -> None:
    """Write the register data to an ISO-dated CSV file with an appropriate header."""
    spreadsheet_name = CSV_FOLDER / (str(datetime.date.today()) + '.csv')
    header = ['Name', 'Phone', 'Email', 'Firm', 'Address', 'Registered as']
    with spreadsheet_name.open('w', encoding="utf-8", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(data)

def write_raw_html(rawHTML: str) -> None:
    """Testing function to dump the HTML to a txt file instead of parsing and writing to csv."""
    with open("registerDump.txt", 'w', encoding="utf-8") as f:
        f.write(rawHTML)
        
def append_to_date_table(dirPath: Path, dates: list[str]):
    """Map dates with unchanged data to an older date with identical data."""
    table = dirPath / ("date_table.txt")
    with open(table, 'a', encoding="utf-8") as f:
        f.write(f"{dates[0]} : {dates[1]}\n")
        
def clean_csvs(dirPath: Path, recentOnly: bool):
    filepaths = get_csv_filepaths(dirPath)
    i = 0
    if recentOnly:
        i = len(filepaths) - 2
    j = i + 1
    while True:
        if j == len(filepaths):
            return
        csv1 = filepaths[i]
        csv2 = filepaths[j]
        if cmp(csv1, csv2, shallow=False):
            append_to_date_table(dirPath, filepaths_to_dates([csv2, csv1]))
            os.remove(csv2)
            j += 1
        else:
            i = j
            j += 1
        
def get_csv_filepaths(dirPath: Path) -> list[Path]:
    """Returns a list of filepaths to all the csv files in time order."""
    # ISO naming format means default sort will time-order
    return sorted(list(dirPath.glob('*.csv')))

def dates_to_filepaths(dates: list[str]) -> list[Path]:
    all_paths = get_csv_filepaths(CSV_FOLDER)
    return select_filepaths_for_dates(all_paths, dates)

def filepaths_to_dates(paths: list[Path]) -> list[str]:
    return [path.stem for path in paths]

def select_filepaths_for_dates(filepaths: list[Path], dates: list[str]) -> list[Path]:
    """Returns a list of paths to files with names matching input dates."""
    datePaths=[]
    for date in dates:
        validate_date(date)
        datePath = next((path for path in filepaths if date in str(path)), None)
        if datePath == None: 
            raise ValueError(f"No file exists for {date}")
        datePaths.append(datePath)

    return datePaths

def validate_date(date: str) -> None:
    """Raises an error if <date> is not in ISO format."""
    try:
        datetime.date.fromisoformat(date)
    except ValueError:
        raise ValueError("Missing or incorrectly formatted date, should be YYYY-MM-DD")
    
def read_date_table(dirPath: Path) -> dict[str:str]:
    table = dirPath / ("date_table.txt")
    d = {}
    with open(table, 'r', encoding="utf-8") as f:
        for line in f:
            (key, val) = line.split(" : ")
            d[key] = val.strip()
    return d
     
def check_already_scraped(dirPath: Path) -> bool:
    date = str(datetime.date.today())
    return (date in get_dates(num=1, dirPath=dirPath)) or (date in read_date_table(dirPath))

def get_dates(num: int, oldest: bool = False, dirPath: Path = CSV_FOLDER) -> list[str]:
    """Gets <num> dates from the newest or oldest existing csv filepaths."""
    filepaths = get_csv_filepaths(dirPath)
    dates = filepaths_to_dates(filepaths)
    if oldest:
        dates = sorted(dates)[:num]
    else:
        dates = sorted(dates)[-num:]
    return dates

def count_dates(dirPath: Path = CSV_FOLDER) -> int:
    return len(get_csv_filepaths(dirPath))