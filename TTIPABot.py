import requests

from ln_auth import auth, headers, user_info

from bs4 import BeautifulSoup, Tag
import csv
import datetime

from pathlib import Path

import pandas as pd

CSV_FOLDER = "TTIPAB register saves"


def TTIPABrequest(count):
    # Public API endpoint as determined by Inspect Element > Network > Requests on Google Chrome
    urlBase = "https://www.ttipattorney.gov.au//sxa/search/results/"
    urlOptions1 = "?s={21522AF6-8499-4C63-8CFA-02E2B97737BE}&itemid={8B94FE47-304A-4629-AD46-DD208EEF71AA}&sig=als&e=0&p="
    urlOptions2 = "&v=%7B2FCA44D4-EE00-43EC-BBBF-858C31387413%7D"
    url =  f"{urlBase}{urlOptions1}{count}{urlOptions2}"
    return requests.get(url)

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

    # Parse and extract all the data
    soup = BeautifulSoup(rawHTML, 'lxml')

    results = soup.find_all(class_="list-item attorney")

    return results

def getRegistrations(result):
    # Check tags for registrations, convert to comma separated string
    registeredAs = []
    for tag in result.find_all(class_="ipr-tag"):
        registeredAs += tag.contents
    
    registeredAs = ", ".join(registeredAs)

    return registeredAs

def getPhoneNumber(result):
    # Get phone numbers
    if not result.find(class_="block-1"): 
        return ""
    
    for child in result.find(class_="block-1").children:
        if isinstance(child, Tag) and child.a:
            phone = child.a.contents[0]

    return phone

def getEmail(result):
    # Get emails
    if not result.find(class_="block-2"): 
        return ""
    
    for child in result.find(class_="block-2").children:
        if isinstance(child, Tag) and child.a:
            email = child.a.contents[0]

    return email

def getFirmAndAddress(result):
        # Get firm and address
    firm = ""
    address = ""
    for block in result.find_all(class_="block"):
        firmFlag = False
        addressFlag = False
        for span in block.find_all('span'):
            if span.contents[0] == " Firm ": 
                firmFlag = True
            elif span.contents[0] == " Address ":
                addressFlag = True
            elif firmFlag:
                firm = span.contents[0].strip()
                firmFlag = False
            elif addressFlag:
                address = span.contents[0].strip()
                addressFlag = False
    
    return firm, address


def extractData(results):
    data = []

    for result in results:
        # Skip blank name entries
        name = result.h4.contents
        if not name: continue
        name = result.h4.contents[0]

        registeredAs = getRegistrations(result)
        phone = getPhoneNumber(result)
        email = getEmail(result)
        (firm, address) = getFirmAndAddress(result)

        data.append([name, phone, email, firm, address, registeredAs])

    return data

def writeToCSV(data):
    #Print the register contents to a CSV file
    spreadsheet_name = Path.cwd() / "TTIPAB register saves" / (str(datetime.date.today()) + '.csv')

    header = ['Name', 'Phone', 'Email', 'Firm', 'Address', 'Registered as']

    # open the file in the write mode
    with spreadsheet_name.open('w', encoding="utf-8", newline='') as f:
        
        writer = csv.writer(f)

        # write header to the csv file
        writer.writerow(header)

        # write data to the csv file
        writer.writerows(data)

def writeRawHTML(rawHTML):
    with open("registerHTML.txt", 'w', encoding="utf-8") as f:
        f.write(rawHTML)

def scrape():
    results = getFullRegister()
    data = extractData(results)
    writeToCSV(data)

def getLatestCsvs():
    # Get filepaths of all the csv files
    folderPath = Path.cwd() / CSV_FOLDER
    csvFilenames = list(folderPath.glob('*.csv'))

    # Take the last two entries - WARNING: ASSUMES ALPHABETICAL SORTING. SHOULD ENFORCE
    date1_path = csvFilenames[-2]
    date2_path = csvFilenames[-1]

    return date1_path, date2_path

def getSpecifiedCsvs(date1, date2):
    
    # Ensure date1 is the earliest date, so later code can assume this
    FORMAT = "%Y-%m-%d"
    if datetime.datetime.strptime(date1, FORMAT) > datetime.datetime.strptime(date2, FORMAT):
        date1, date2 = date2, date1

    date1_path = Path.cwd() / CSV_FOLDER / (date1 + ".csv")
    date2_path = Path.cwd() / CSV_FOLDER / (date2 + ".csv")

    return date1_path, date2_path

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

def analyse(date1_path, date2_path):
    # Data comparison steps
    (df_date1, df_date2) = createDataframes(date1_path, date2_path)
    (df_left, df_right) = getDiffs(df_date1, df_date2)
    

    # Find which names are new
    df_names = pd.merge(df_left, df_right, on='Name', how="outer", indicator="NameExist")

    df_newAttorneys = df_names.query("NameExist == 'right_only'")
    df_lapsedAttorneys = df_names.query("NameExist == 'left_only'")
    df_changedDetails = df_names.query("NameExist == 'both'")
    df_changedDetails = df_changedDetails.fillna('')

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

def writeNewAttorneyTweet(newAttorneys):
    # Takes in a dataframe

    if newAttorneys.empty:
        return None
    
    tweet = "Congratulations to the following newly registered IP attorneys: "

    #TODO: Possibly say their registration type

    for newAttorney in newAttorneys.itertuples():
        tweet += newAttorney.Name 
        if newAttorney.Firm_y != '':
            tweet += f" of {newAttorney.Firm_y}"

        tweet += ", "
        
    tweet = fixGrammar(tweet)

    return tweet

def writeFirmChangeTweet(firmChanges):
    # Takes in a dataframe

    if firmChanges.empty:
        return None

    tweet = "The following IP attorneys have recently changed firm: "

    #TODO: Maybe tidy up a little

    for firmChange in firmChanges.itertuples():
        noFirmSubstitute = "independent"

        tweet += f"{firmChange.Name} from " 
        tweet += f"{firmChange.Firm_x}" if firmChange.Firm_x != '' else noFirmSubstitute

        tweet += " to "
        tweet += f"{firmChange.Firm_y}" if firmChange.Firm_y != '' else noFirmSubstitute

        tweet += ", "
    
    tweet = fixGrammar(tweet)

    return tweet


def linkedInPost(tweets):
    if not tweets:
        #TODO put some logic here instead if it's decided no changes should still result in a post
        return

    credentials = 'credentials.json'
    access_token = auth(credentials)
    headers_ = headers(access_token) # Make the headers to attach to the API call.
    
    # Get user id to make a post
    user_info_ = user_info(headers_)
    urn = user_info_['id']
    
    # Newest Shares API
    api_url = 'https://api.linkedin.com/rest/posts'
    author = f'urn:li:person:{urn}'
    
    message = "AUTOMATED TEST POST\n\n"
    for tweet in tweets:
        message += tweet + "\n\n"

    link = 'https://github.com/Tradeylouish/TTIPABot'
    message += link
    
    post_data = {
    "author": author,
    "commentary": message,
    "visibility": "PUBLIC",
    "distribution": {
        "feedDistribution": "MAIN_FEED",
        "targetEntities": [],
        "thirdPartyDistributionChannels": []
    },
    "lifecycleState": "PUBLISHED",
    "isReshareDisabledByAuthor": True
    }
    
    print(message)

    #r = requests.post(api_url, headers=headers_, json=post_data)
    #r.json()


if __name__ == '__main__':
    #scrape()
    (csv1, csv2) = getLatestCsvs()
    #(csv1, csv2) = getSpecifiedCsvs("2023-01-27", "2023-03-17")

    (newAttorneys, firmChanges) = analyse(csv1, csv2)
    
    newAttorneyTweet = writeNewAttorneyTweet(newAttorneys)
    firmChangeTweet = writeFirmChangeTweet(firmChanges)

    # Compile the tweets and filter out None values
    tweets = [newAttorneyTweet, firmChangeTweet]
    tweets = list(filter(lambda item: item is not None, tweets))
    
    #TODO Should a linkedIn post be made to report no changes?
    if not tweets:
        print("No recent changes to the register.")
    else:
        #TODO decouple linkedin API stuff from printing draft posts
        for tweet in tweets:
            print(tweet)
        #linkedInPost(tweets)