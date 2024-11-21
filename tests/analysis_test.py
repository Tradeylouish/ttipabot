from pathlib import Path
import pytest
import pandas as pd
from ttipabot import analyser

EXAMPLES_FOLDER = Path.cwd() / "tests/Examples"

@pytest.fixture
def examples():
    return analyser.csvs_to_dfs([EXAMPLES_FOLDER / "csvExample1.csv", EXAMPLES_FOLDER / "csvExample2.csv"])

def test_csv_to_df(examples):
    assert not examples[0].empty
    assert type(examples[0]) == pd.DataFrame

def test_name_rank_df(examples):
    ranked_df = analyser.name_rank_df(examples[0], 3)
    assert ranked_df.iloc[0]['Name'] == "Angela Aitchison Searle"
    assert ranked_df.iloc[1]['Name'] == "Daniel Bolderston"
    assert ranked_df.iloc[2]['Name'] == "Michelle Catto"

def test_attorneys_df_to_lines(examples):
    exampleLines = ["Daniel Bolderston of Allens Patent and Trade Marks Attorneys.",
                    "Michelle Catto of FB Rice Pty Ltd.",
                    "Angela Aitchison Searle."]

    assert analyser.attorneys_df_to_lines(examples[0]) == exampleLines

def test_compare_csvs(examples):
    df_diffs = analyser.get_diffs_df(examples[0], examples[1])
    df_newAttorneys = analyser.get_new_attorneys_df(df_diffs)
    df_changedFirms = analyser.get_firmChanges_df(df_diffs)
    assert df_newAttorneys.iloc[0]['Name'] == "Albert Abram"
    assert df_changedFirms.iloc[0]['Name'] == "Daniel Bolderston" and df_changedFirms.iloc[0]['New firm'] == "AJ Park"


def test_filter_attorneys(examples):
    assert analyser.filter_attorneys(examples[0], pat=True, tm=False).equals(examples[0][1:3])