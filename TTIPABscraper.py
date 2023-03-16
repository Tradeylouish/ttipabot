import requests
from bs4 import BeautifulSoup
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

# Write the HTML to a file for intermdiate stage - reduces API pings
with open("registerHTML.txt", 'w', encoding="utf-8") as f:
    f.write(rawHTML)