import pytest
from bs4 import BeautifulSoup, Tag
from ttipabot import scraper
from pathlib import Path

EXAMPLES_FOLDER = Path.cwd() / "tests/Examples"

class ExampleAttorney:
    def __init__(self, rawHTML, allData, index):
        self.rawHTML = rawHTML
        self.allData = allData
        self.name = allData[0]
        self.phone = allData[1]
        self.email = allData[2]
        self.firm = allData[3]
        self.address = allData[4]
        self.registrations =allData[5]
        self.index=index

class Examples:
    def __init__(self):
        exampleHTML = ["blankAttorneyExample.txt","attorneyHTMLExample.txt","attorneyHTMLExample2.txt"]
        exampleData = [["","","","","",""],
                       ["Louis Francisco Yates Habberfield-Short", 
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
        self.exampleAttorneys=[ExampleAttorney(self.read_example_attorney(exampleHTML[i]), exampleData[i], i) for i in range(3)]

    def read_example_attorney(self, filename: str):
        """Helper function for setting up example attorney HTML to test on."""
        rawHTML = ""
        with open(EXAMPLES_FOLDER / filename, 'r', encoding="utf-8") as f:
            rawHTML = f.read()
        soup = BeautifulSoup(rawHTML, 'lxml')
        return soup.find(class_="list-item attorney")


@pytest.fixture(scope="session")
def examples() -> Examples:
    return Examples()

def test_name_parse(examples: Examples):
    for attorney in examples.exampleAttorneys:
        assert scraper.get_contact_data(attorney.rawHTML, " Attorney ") == attorney.name, f"Attorney {attorney.index} should be {attorney.name}"

def test_phone_parse(examples: Examples):
    for attorney in examples.exampleAttorneys:
        assert scraper.get_contact_data(attorney.rawHTML, " Phone ") == attorney.phone, f"Attorney {attorney.index} should be {attorney.phone}"

def test_email_parse(examples: Examples):
    for attorney in examples.exampleAttorneys:
        assert scraper.get_contact_data(attorney.rawHTML, " Email ") == attorney.email, f"Attorney {attorney.index} should be {attorney.email}"

def test_firm_parse(examples: Examples):
    for attorney in examples.exampleAttorneys:
        assert scraper.get_contact_data(attorney.rawHTML, " Firm ") == attorney.firm, f"Attorney {attorney.index} should be {attorney.firm}"

def test_address_parse(examples: Examples):
    for attorney in examples.exampleAttorneys:
        assert scraper.get_contact_data(attorney.rawHTML, " Address ") == attorney.address, f"Attorney {attorney.index} should be {attorney.address}"

def test_registrations_parse(examples: Examples):
    for attorney in examples.exampleAttorneys:
        assert scraper.get_contact_data(attorney.rawHTML, " Registered as") == attorney.registrations, f"Attorney {attorney.index} should be {attorney.registrations}"

def test_all_data_parse(examples: Examples):
    for attorney in examples.exampleAttorneys:
        assert scraper.get_attorney_data(attorney.rawHTML) == attorney.allData

def test_multiple_attorneys_data_parse(examples: Examples):
    data = [examples.exampleAttorneys[1].allData, examples.exampleAttorneys[2].allData]
    html = [attorney.rawHTML for attorney in examples.exampleAttorneys]
    assert scraper.parse_register(html) == data