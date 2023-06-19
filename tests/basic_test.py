import pytest
import ttipabot

def test_one():
    assert ttipabot.testFunction(1, 2) == 3, "should be 3"
    
def test_two():
    assert ttipabot.testFunction(1, 3) == 5, "should be 5"

#TODO add tests that read in example register HTML, dataframes etc.