import pytest
from bs4 import BeautifulSoup, Tag
import ttipabot

# Setting up example attorney HTML to test on
def read_example_attorney(filename):
    rawHTML = ""

    with open(filename, 'r', encoding="utf-8") as f:
        rawHTML = f.read()
    soup = BeautifulSoup(rawHTML, 'lxml')
    return soup.find(class_="list-item attorney")

firstExampleAttorney = read_example_attorney("attorneyHTMLexample.txt")
secondExampleAttorney = read_example_attorney("attorneyHTMLexample2.txt")

def test_name_parse():
    exampleName = "Louis Francisco Yates Habberfield-Short"
    assert ttipabot.getContactData(firstExampleAttorney, " Attorney ") == exampleName, f"should be {exampleName}"

def test_phone_parse():
    examplePhoneNumber = "+64 9 353 5423"
    assert ttipabot.getContactData(firstExampleAttorney, " Phone ") == examplePhoneNumber, f"should be {examplePhoneNumber}"        

def test_email_parse():
    exampleEmail = "louis.habberfield-short@ajpark.com"
    assert ttipabot.getContactData(firstExampleAttorney, " Email ") == exampleEmail, f"should be {exampleEmail}"

def test_firm_parse():
    #With no listed firm
    exampleFirm = ""
    assert ttipabot.getContactData(firstExampleAttorney, " Firm ") == exampleFirm, f"should be {exampleFirm}"

    #With listed firm
    exampleFirm = "Collison & Co"
    assert ttipabot.getContactData(secondExampleAttorney, " Firm ") == exampleFirm, f"should be {exampleFirm}"

def test_registrations_parse():
    # With a single registered attorney
    exampleRegistrations = "Patents"
    assert ttipabot.getContactData(firstExampleAttorney, " Registered as") == exampleRegistrations, f"should be {exampleRegistrations}"

    exampleRegistrations = "Patents, Trade marks"
    # With a dual registered attorney
    assert ttipabot.getContactData(secondExampleAttorney, " Registered as") == exampleRegistrations, f"should be {exampleRegistrations}"

def test_address_parse():
    firstExampleAddress = "Level 14, Aon Centre, 29 Customs Street West, Auckland 1010, New Zealand"
    assert ttipabot.getContactData(firstExampleAttorney, " Address ") == firstExampleAddress, f"should be {firstExampleAddress}"

def test_all_data_parse():
    exampleData = ["Louis Francisco Yates Habberfield-Short", 
                   "+64 9 353 5423", 
                   "louis.habberfield-short@ajpark.com", 
                   "", 
                   "Level 14, Aon Centre, 29 Customs Street West, Auckland 1010, New Zealand", 
                   "Patents"]
    
    assert ttipabot.getAttorneyData(firstExampleAttorney) == exampleData