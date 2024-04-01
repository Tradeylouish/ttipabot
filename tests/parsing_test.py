import pytest
from bs4 import BeautifulSoup, Tag
import ttipabot
from pathlib import Path

EXAMPLES_FOLDER = Path.cwd() / "tests/Examples"

# Helper function for setting up example attorney HTML to test on
def read_example_attorney(filename):
    rawHTML = ""

    with open(EXAMPLES_FOLDER / filename, 'r', encoding="utf-8") as f:
        rawHTML = f.read()
    soup = BeautifulSoup(rawHTML, 'lxml')
    return soup.find(class_="list-item attorney")

# Globally accessible attorney examples
firstExampleAttorney = read_example_attorney("attorneyHTMLExample.txt")
secondExampleAttorney = read_example_attorney("attorneyHTMLExample2.txt")
blankAttorney = read_example_attorney("blankAttorneyExample.txt")

def test_name_parse():
    exampleName = "Louis Francisco Yates Habberfield-Short"
    assert ttipabot.get_contact_data(firstExampleAttorney, " Attorney ") == exampleName, f"should be {exampleName}"

    exampleName = ""
    assert ttipabot.get_contact_data(blankAttorney, " Attorney ") == exampleName, f"should be {exampleName}"

def test_phone_parse():
    examplePhoneNumber = "+64 9 353 5423"
    assert ttipabot.get_contact_data(firstExampleAttorney, " Phone ") == examplePhoneNumber, f"should be {examplePhoneNumber}"

    examplePhoneNumber = ""
    assert ttipabot.get_contact_data(blankAttorney, " Phone ") == examplePhoneNumber, f"should be {examplePhoneNumber}"  

def test_email_parse():
    exampleEmail = "louis.habberfield-short@ajpark.com"
    assert ttipabot.get_contact_data(firstExampleAttorney, " Email ") == exampleEmail, f"should be {exampleEmail}"

def test_firm_parse():
    #With no listed firm
    exampleFirm = ""
    assert ttipabot.get_contact_data(firstExampleAttorney, " Firm ") == exampleFirm, f"should be {exampleFirm}"

    #With listed firm
    exampleFirm = "Collison & Co"
    assert ttipabot.get_contact_data(secondExampleAttorney, " Firm ") == exampleFirm, f"should be {exampleFirm}"

def test_registrations_parse():
    # With a single registered attorney
    exampleRegistrations = "Patents"
    assert ttipabot.get_contact_data(firstExampleAttorney, " Registered as") == exampleRegistrations, f"should be {exampleRegistrations}"

    exampleRegistrations = "Patents, Trade marks"
    # With a dual registered attorney
    assert ttipabot.get_contact_data(secondExampleAttorney, " Registered as") == exampleRegistrations, f"should be {exampleRegistrations}"

def test_address_parse():
    firstExampleAddress = "Level 14, Aon Centre, 29 Customs Street West, Auckland 1010, New Zealand"
    assert ttipabot.get_contact_data(firstExampleAttorney, " Address ") == firstExampleAddress, f"should be {firstExampleAddress}"

def test_all_data_parse():
    exampleData = ["Louis Francisco Yates Habberfield-Short", 
                   "+64 9 353 5423", 
                   "louis.habberfield-short@ajpark.com", 
                   "", 
                   "Level 14, Aon Centre, 29 Customs Street West, Auckland 1010, New Zealand", 
                   "Patents"]
    
    assert ttipabot.get_attorney_data(firstExampleAttorney) == exampleData

def test_multiple_attorneys_data_parse():

    exampleAttorneys = [blankAttorney, firstExampleAttorney, secondExampleAttorney]
    exampleData = [["Louis Francisco Yates Habberfield-Short", 
                "+64 9 353 5423", 
                "louis.habberfield-short@ajpark.com", 
                "", 
                "Level 14, Aon Centre, 29 Customs Street West, Auckland 1010, New Zealand", 
                "Patents"], 
                ["Donald Iain Angus", 
                "08 8212 3133", 
                "collison@collison.com.au", 
                "Collison & Co", 
                "Level 4 70 Light Square Adelaide SA 5000 Australia", 
                "Patents, Trade marks"]
                ]

    assert ttipabot.parse_register(exampleAttorneys) == exampleData