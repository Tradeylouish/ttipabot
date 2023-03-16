import requests
from bs4 import BeautifulSoup, Tag
import re
import csv
import datetime


def TTIPABrequest(count):
    # Public API endpoint as determined by Inspect Element > Network > Requests on Google Chrome
    url = "https://www.ttipattorney.gov.au//sxa/search/results/?s={21522AF6-8499-4C63-8CFA-02E2B97737BE}&itemid={8B94FE47-304A-4629-AD46-DD208EEF71AA}&sig=als&e=0&p=" + str(count) + "&v=%7B2FCA44D4-EE00-43EC-BBBF-858C31387413%7D"
    return requests.get(url)


#Do an intial ping of the register to determine the total number of results to be requested
initialResponse = TTIPABrequest(1)
#Convert JSON response to dict and extract count
resultsCount = str(initialResponse.json().get("Count"))


#Request the full contents of the register
rawHTML = TTIPABrequest(resultsCount).text
# Get rid of control characters
rawHTML = rawHTML.replace("\\r", "")
rawHTML = rawHTML.replace("\\n", "")
rawHTML = rawHTML.replace("\\", "")

# Parse and extract all the data
soup = BeautifulSoup(rawHTML, 'lxml')

results = soup.find_all(class_="list-item attorney")

data = []

for result in results:
    # Skip blank name entries
    name = result.h4.contents
    if not name: continue
    name = result.h4.contents[0]

    # Check tags for registrations, convert to comma separated string
    registeredAs = []
    for tag in result.find_all(class_="ipr-tag"):
        registeredAs += tag.contents
    
    registeredAs = ", ".join(registeredAs)
    
    # Get phone numbers
    if not result.find(class_="block-1"): 
        phone = ""
    else: 
        for child in result.find(class_="block-1").children:
            if isinstance(child, Tag) and child.a:
                phone = child.a.contents[0]

    # Get emails
    if not result.find(class_="block-2"): 
        email = ""
    else: 
        for child in result.find(class_="block-2").children:
            if isinstance(child, Tag) and child.a:
                email = child.a.contents[0]

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

    data.append([name, phone, email, firm, address, registeredAs])


#Print the register contents to a CSV file
spreadsheet_name = "TTIPAB register " + str(datetime.date.today()) + '.csv' 

header = ['uid', 'Name', 'Phone', 'Email', 'Firm', 'Address', 'Registered as']

# open the file in the write mode
with open(spreadsheet_name, 'w', encoding="utf-8", newline='') as f:
    # create the csv writer
    writer = csv.writer(f)

    # write header to the csv file
    writer.writerow(header)

    # write data to the csv file
    writer.writerows(data)