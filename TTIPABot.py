import requests
from bs4 import BeautifulSoup, Tag
import re
import csv
import datetime

from pathlib import Path

import pandas as pd
import  xlwings as xw

import tweepy

class TTIPABot:
    def __init__(self):
        print("Initialised")


    def TTIPABrequest(self, count):
        # Public API endpoint as determined by Inspect Element > Network > Requests on Google Chrome
        urlBase = "https://www.ttipattorney.gov.au//sxa/search/results/"
        urlOptions1 = "?s={21522AF6-8499-4C63-8CFA-02E2B97737BE}&itemid={8B94FE47-304A-4629-AD46-DD208EEF71AA}&sig=als&e=0&p="
        urlOptions2 = "&v=%7B2FCA44D4-EE00-43EC-BBBF-858C31387413%7D"
        url =  urlBase + urlOptions1 + str(count) + urlOptions2
        return requests.get(url)

    def getFullRegister(self):
        #Do an intial ping of the register to determine the total number of results to be requested
        initialResponse = self.TTIPABrequest(1)
        #Convert JSON response to dict and extract count
        resultsCount = initialResponse.json().get("Count")

        #Request the full contents of the register
        rawHTML = self.TTIPABrequest(resultsCount).text
        # Get rid of control characters
        rawHTML = rawHTML.replace("\\r", "")
        rawHTML = rawHTML.replace("\\n", "")
        rawHTML = rawHTML.replace("\\", "")

        # Parse and extract all the data
        soup = BeautifulSoup(rawHTML, 'lxml')

        results = soup.find_all(class_="list-item attorney")

        return results

    def getRegistrations(self, result):
        # Check tags for registrations, convert to comma separated string
        registeredAs = []
        for tag in result.find_all(class_="ipr-tag"):
            registeredAs += tag.contents
        
        registeredAs = ", ".join(registeredAs)

        return registeredAs
    
    def getPhoneNumber(self, result):
        # Get phone numbers
        if not result.find(class_="block-1"): 
            return ""
        
        for child in result.find(class_="block-1").children:
            if isinstance(child, Tag) and child.a:
                phone = child.a.contents[0]

        return phone

    def getEmail(self, result):
        # Get emails
        if not result.find(class_="block-2"): 
            return ""
        
        for child in result.find(class_="block-2").children:
            if isinstance(child, Tag) and child.a:
                email = child.a.contents[0]

        return email
    
    def getFirmAndAddress(self, result):
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
    

    def extractData(self, results):
        data = []

        for result in results:
            # Skip blank name entries
            name = result.h4.contents
            if not name: continue
            name = result.h4.contents[0]

            registeredAs = self.getRegistrations(result)
            phone = self.getPhoneNumber(result)
            email = self.getEmail(result)
            (firm, address) = self.getFirmAndAddress(result)

            data.append([name, phone, email, firm, address, registeredAs])

        return data

    def writeToCSV(self, data):
        #Print the register contents to a CSV file
        spreadsheet_name = "TTIPAB register " + str(datetime.date.today()) + '.csv' 

        header = ['Name', 'Phone', 'Email', 'Firm', 'Address', 'Registered as']

        # open the file in the write mode
        with open(spreadsheet_name, 'w', encoding="utf-8", newline='') as f:
            # create the csv writer
            writer = csv.writer(f)

            # write header to the csv file
            writer.writerow(header)

            # write data to the csv file
            writer.writerows(data)

    def writeRawHTML(self, rawHTML):
        with open("registerHTML.txt", 'w', encoding="utf-8") as f:
            f.write(rawHTML)

    def scrape(self):
        results = self.getFullRegister()
        data = self.extractData(results)
        self.writeToCSV(data)

    def getFilePaths(self):
        # Get filepaths of all the csv files
        csvFilenames = list(Path.cwd().glob('*.csv'))

        # Take the last two entries - WARNING: ASSUMES ALPHABETICAL SORTING. SHOULD ENFORCE
        date1_path = csvFilenames[-2]
        date2_path = csvFilenames[-1]

        return date1_path, date2_path

    def createDataframes(self, date1_path, date2_path):

        #Read the CSV data into dataframes
        df_date1 = pd.read_csv(date1_path)
        df_date2 = pd.read_csv(date2_path)

        #
        #diff = df_date2.compare(df_date1, align_axis=1)

        # Reset the index
        df_date2 = df_date2.reset_index()

        return df_date1, df_date2
    
    def getDiffs(self, df_date1, df_date2):

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
    
    def tweet(self):
        # Data comparison steps
        (date1_path, date2_path) = self.getFilePaths()
        (df_date1, df_date2) = self.createDataframes(date1_path, date2_path)
        (df_left, df_right) = self.getDiffs(df_date1, df_date2)
        

        # Find which names are new
        df_names = pd.merge(df_left, df_right, on='Name', how="outer", indicator="NameExist")

        df_newAttorneys = df_names.query("NameExist == 'right_only'")
        df_lapsedAttorneys = df_names.query("NameExist == 'left_only'")
        df_changedAttorneys = df_names.query("NameExist == 'both'")

        print(df_changedAttorneys)

        print('The followng attorneys are newly registered:')
        print(df_newAttorneys[['Name', 'Firm_y']])
        print('The followng attorneys have updated details:')
        print(df_changedAttorneys[['Name', 'Firm_x', 'Firm_y']])


if __name__ == '__main__':
    ttipa_bot = TTIPABot()
    #ttipa_bot.scrape()
    ttipa_bot.tweet()

    #print(ttipa_bot.getFilePaths())