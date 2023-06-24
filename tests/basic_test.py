import pytest
from bs4 import BeautifulSoup, Tag
import ttipabot

def test_parsing():
    rawHTML = ""

    with open("attorneyHTMLExample.txt", 'r', encoding="utf-8") as f:
        rawHTML = f.read()
    soup = BeautifulSoup(rawHTML, 'lxml')
    attorney = soup.find(class_="list-item attorney")

    #print(attorney)

    assert ttipabot.getPhoneNumber(attorney) == "+64 9 353 5423", "should be +64 9 353 5423"

    assert ttipabot.getEmail(attorney) == "louis.habberfield-short@ajpark.com", "should be louis.habberfield-short@ajpark.com"

    assert ttipabot.getAddress(attorney) == "Level 14, Aon Centre, 29 Customs Street West, Auckland 1010, New Zealand", "should be "



#TODO add tests that read in example register HTML, dataframes etc.