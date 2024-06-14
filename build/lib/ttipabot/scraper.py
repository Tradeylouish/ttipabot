import datetime
import csv
from pathlib import Path
import logging

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

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

def write_to_csv(data: list[list[str]], folderpath: Path) -> None:
    """Write the register data to an ISO-dated CSV file with an appropriate header."""
    spreadsheet_name = folderpath / (str(datetime.date.today()) + '.csv')
    header = ['Name', 'Phone', 'Email', 'Firm', 'Address', 'Registered as']
    with spreadsheet_name.open('w', encoding="utf-8", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(data)

def write_raw_html(rawHTML: str) -> None:
    """Testing function to dump the HTML to a txt file instead of parsing and writing to csv."""
    with open("registerDump.txt", 'w', encoding="utf-8") as f:
        f.write(rawHTML)