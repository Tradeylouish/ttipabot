import requests

import click

from bs4 import BeautifulSoup, Tag
import csv
import datetime

from pathlib import Path

import pandas as pd

CSV_FOLDER = Path.cwd() / "TTIPAB register saves"

@click.group()
def cli():
    pass


def TTIPABrequest(count):
    # Public API endpoint as determined by Inspect Element > Network > Requests on Google Chrome
    urlBase = "https://www.ttipattorney.gov.au//sxa/search/results/"
    urlOptions1 = "?s={21522AF6-8499-4C63-8CFA-02E2B97737BE}&itemid={8B94FE47-304A-4629-AD46-DD208EEF71AA}&sig=als&e=0&p="
    urlOptions2 = "&v=%7B2FCA44D4-EE00-43EC-BBBF-858C31387413%7D"
    url =  f"{urlBase}{urlOptions1}{count}{urlOptions2}"
    return requests.get(url, stream=True)

def getFullRegister():
    #Do an intial ping of the register to determine the total number of results to be requested
    initialResponse = TTIPABrequest(1)
    #Convert JSON response to dict and extract count
    resultsCount = initialResponse.json().get("Count")

    #Request the full contents of the register
    rawHTML = TTIPABrequest(resultsCount).text
    # Get rid of control characters
    rawHTML = rawHTML.replace("\\r", "")
    rawHTML = rawHTML.replace("\\n", "")
    rawHTML = rawHTML.replace("\\", "")

    #writeRawHTML(rawHTML)

    # Parse and extract all the data
    soup = BeautifulSoup(rawHTML, 'lxml')

    attorneys = soup.find_all(class_="list-item attorney")

    return attorneys

def getContactData(result, searchString):
    tag = result.find("span", string=searchString)
    if tag is None:
        return ""
    
    #Data is always in (non-whitespace) descendant string(s) of the tag that follows
    #Could be two strings for dual registrations, so comma join
    return ", ".join(tag.find_next_sibling().stripped_strings) 

def getAttorneyData(attorney):
    #Takes a soup representing an attorney
    fields = [" Attorney ", " Phone ", " Email ", " Firm ", " Address ", " Registered as"]
    return [getContactData(attorney, field) for field in fields]

def parseRegister(attorneys):
    #Takes a list of soup objects representing attorneys
    data = [getAttorneyData(attorney) for attorney in attorneys 
            if getContactData(attorney, " Attorney ") != ""]

    return data

def writeToCSV(data, folderpath):
    #Print the register contents to a CSV file
    spreadsheet_name = folderpath / (str(datetime.date.today()) + '.csv')

    header = ['Name', 'Phone', 'Email', 'Firm', 'Address', 'Registered as']

    # open the file in the write mode
    with spreadsheet_name.open('w', encoding="utf-8", newline='') as f:
        
        writer = csv.writer(f)

        # write header to the csv file
        writer.writerow(header)

        # write data to the csv file
        writer.writerows(data)

def writeRawHTML(rawHTML):
    with open("registerDump.txt", 'w', encoding="utf-8") as f:
        f.write(rawHTML)

@cli.command()
def scrape():
    results = getFullRegister()
    data = parseRegister(results)
    writeToCSV(data, CSV_FOLDER)

def getCsvFilepaths(folderPath):
    return list(folderPath.glob('*.csv'))

def getLatestCsvs(csvFilepaths):
    # Filename format means default sort will time-order
    csvFilepaths.sort()

    # Return the last two entries
    return csvFilepaths[-2], csvFilepaths[-1]

def getSpecifiedCsvs(csvFilepaths, dates):
    # Look for a filepath that contain the date string
    datePaths = [next((path for path in csvFilepaths if date in str(path)), None) for date in dates]

    return datePaths

def createDataframes(date1_path, date2_path):

    #Read the CSV data into dataframes
    df_date1 = pd.read_csv(date1_path, dtype='string')
    df_date2 = pd.read_csv(date2_path, dtype='string')

    # Replace missing values with empty strings for comparison purposes
    df_date1.fillna('')
    df_date2.fillna('')
    #
    #diff = df_date2.compare(df_date1, align_axis=1)

    # Reset the index
    df_date2 = df_date2.reset_index()

    return df_date1, df_date2

def getDiffs(df_date1, df_date2):

    # Merge the dataframes so that differences can be compared
    df_diff = pd.merge(df_date1, df_date2, how="outer", indicator="Exist")

    # Query which rows are different
    df_diff = df_diff.query("Exist != 'both'")

    #print(df_diff)

    # Separate rows that have changed into a pair of dataframes
    df_left = df_diff.query("Exist == 'left_only'")
    df_right = df_diff.query("Exist == 'right_only'")


    # TODO - name change detect logic?
    df_left = df_left.sort_values(by = 'Name')
    df_right = df_right.sort_values(by = 'Name')

    return df_left, df_right

def compareCsvs(date1_path, date2_path):
    # Data comparison steps
    (df_date1, df_date2) = createDataframes(date1_path, date2_path)
    (df_left, df_right) = getDiffs(df_date1, df_date2)
    
    # Find which names are new
    df_names = pd.merge(df_left, df_right, on='Name', how="outer", indicator="NameExist")

    df_newAttorneys = df_names.query("NameExist == 'right_only'")
    df_lapsedAttorneys = df_names.query("NameExist == 'left_only'")
    df_changedDetails = df_names.query("NameExist == 'both'")

    df_changedFirms = df_changedDetails.query("Firm_x != Firm_y")

    #TODO: Consider doing a comparison of registrations and capturing those going from single to dual registered

    # Prep the needed data, replace missing values with empty strings to assist comparisons later on
    df_newAttorneys = df_newAttorneys[['Name', 'Firm_y', 'Registered as_y']].fillna('')
    df_changedFirms = df_changedFirms[['Name', 'Firm_x', 'Firm_y']].fillna('')
    
    return df_newAttorneys, df_changedFirms

def fixGrammar(string):
    # Replace trailing comma with full stop
    string = string[:-2] + "."
    
    lastCommaIndex = string.rfind(",")
    # If there's no comma
    if lastCommaIndex == -1:
        return string
    # Insert 'and'
    return string[ : lastCommaIndex + 2] + "and " + string[lastCommaIndex + 2 : ]

def writeNewAttorneySummary(newAttorneys):
    # Takes in a dataframe

    if newAttorneys.empty:
        return None
    
    summary = "Congratulations to the following newly registered IP attorneys: "

    #TODO: Possibly say their registration type

    for newAttorney in newAttorneys.itertuples():
        summary += newAttorney.Name 
        if newAttorney.Firm_y != '':
            summary += f" of {newAttorney.Firm_y}"

        summary += ", "
        
    summary = fixGrammar(summary)

    return summary

def writeFirmChangeSummary(firmChanges):
    # Takes in a dataframe

    if firmChanges.empty:
        return None

    summary = "The following IP attorneys have recently changed firm: "

    #TODO: Maybe tidy up a little

    for firmChange in firmChanges.itertuples():
        noFirmSubstitute = "independent"

        summary += f"{firmChange.Name} from " 
        summary += f"{firmChange.Firm_x}" if firmChange.Firm_x != '' else noFirmSubstitute

        summary += " to "
        summary += f"{firmChange.Firm_y}" if firmChange.Firm_y != '' else noFirmSubstitute

        summary += ", "
    
    summary = fixGrammar(summary)

    return summary

def getLatestDates(num):

    csvFilepaths = getCsvFilepaths(CSV_FOLDER)

    # Filename format means default sort will time-order
    csvFilepaths.sort()

    # Create a list of strings representing the most recent dates, length equal to num argument
    dates = [Path(csvFilepaths[-i]).stem for i in range(1, num+1)]

    return dates

@cli.command()
@click.option('--date', default=getLatestDates(num=1)[0], help='date to rank name lengths')
@click.option('--num', default=10, help='number of names in top ranking')
def rankNames(date, num):

    #print(dates)
    csvFilepaths = getCsvFilepaths(CSV_FOLDER)
    csv = getSpecifiedCsvs(csvFilepaths, [date])[0]

    #TODO vectorise existing code above

    df = pd.read_csv(csv, dtype='string')

    # Replace missing values with empty strings for comparison purposes
    df.fillna('')

    # Sort names and reindex to show ranking
    df = df.sort_values(by='Name', ascending=False, key=lambda col: col.str.len())
    df.reset_index(inplace=True)
    print(df['Name'].head(num))


@cli.command()
@click.option('--dates', nargs=2, default=getLatestDates(num=2), help='dates to compare')
def compare(dates):

    date1, date2 = dates
    # Ensure date1 is the earliest date, so later code can assume this
    FORMAT = "%Y-%m-%d"
    if datetime.datetime.strptime(date1, FORMAT) > datetime.datetime.strptime(date2, FORMAT):
        date1, date2 = date2, date1
    
    csvFilepaths = getCsvFilepaths(CSV_FOLDER)

    (csv1, csv2) = getSpecifiedCsvs(csvFilepaths, [date1, date2])

    (newAttorneys, firmChanges) = compareCsvs(csv1, csv2)
    
    newAttorneySummary = writeNewAttorneySummary(newAttorneys)
    firmChangeSummary = writeFirmChangeSummary(firmChanges)

    # Compile the summaries and filter out None values
    summaries = [newAttorneySummary, firmChangeSummary]
    summaries = list(filter(lambda item: item is not None, summaries))
    
    if not summaries:
        print("No recent changes to the register.")
        return
    
    for summary in summaries:
        print(summary)

if __name__ == '__main__':
    cli()