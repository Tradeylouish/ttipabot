import datetime
from pathlib import Path
import pandas as pd
from typing import NamedTuple, Iterable

def get_csv_filepaths(dirPath: Path) -> list[Path]:
    """Returns a list of filepaths to all the csv files in time order."""
    # ISO naming format means default sort will time-order
    return sorted(list(dirPath.glob('*.csv')))

def validate_date(date: str) -> None:
    """Raises an error if <date> is not in ISO format."""
    try:
        datetime.date.fromisoformat(date)
    except ValueError:
        raise ValueError("Missing or incorrectly formatted date, should be YYYY-MM-DD")

def select_filepaths_for_dates(filepaths: list[Path], dates: list[str]) -> list[Path]:
    """Returns a list of paths to files with names matching input dates."""
    datePaths=[]
    for date in dates:
        validate_date(date)
        datePath = next((path for path in filepaths if date in str(path)), None)
        if datePath == None: 
            raise ValueError(f"No file exists for {date}")
        datePaths.append(datePath)

    return datePaths

def csv_to_df(csvPath: Path) -> pd.DataFrame:
    """Converts a csv to a dataframe"""
    return pd.read_csv(csvPath, dtype='string').fillna('')

def csvs_to_dfs(datePaths: list[Path]) -> list[pd.DataFrame]:
    """Returns a list of dataframes from a list of filepaths to csvs."""
    #Read the CSV data into dataframes
    return [csv_to_df(datePath) for datePath in datePaths]

def get_diffs_df(df_date1: pd.DataFrame, df_date2: pd.DataFrame) -> pd.DataFrame:
    """Return a dataframe showing all the differences in data between two input dataframes."""
    # Merge the dataframes so that differences can be compared
    df_diff = pd.merge(df_date1, df_date2, how="outer", indicator="Exist")

    # Query which rows are different
    df_diff = df_diff.query("Exist != 'both'")

    # Separate rows that have changed into a pair of dataframes
    df_left = df_diff.query("Exist == 'left_only'").sort_values(by = 'Name')
    df_right = df_diff.query("Exist == 'right_only'").sort_values(by = 'Name')

    return pd.merge(df_left, df_right, on='Name', how="outer", indicator="NameExist")

def get_new_attorneys_df(df_diffs: pd.DataFrame) -> pd.DataFrame:
    # TODO: Consider doing a comparison of registrations and capturing those going from single to dual registered
    df_newAttorneys = df_diffs.query("NameExist == 'right_only'")
    # Prep the needed data, replace missing values with empty strings to assist comparisons later on
    df_newAttorneys = df_newAttorneys[['Name', 'Firm_y', 'Registered as_y']].fillna('')
    # Reformat for readability
    df_newAttorneys = df_newAttorneys.rename(columns={"Firm_y": "Firm", "Registered as_y": "Registered as"}).reset_index(drop=True)
    df_newAttorneys.index += 1
    return df_newAttorneys

def get_firmChanges_df(df_diffs: pd.DataFrame) -> pd.DataFrame:
    df_changedDetails = df_diffs.query("NameExist == 'both'")
    # TODO - name change detect logic?
    df_changedFirms = df_changedDetails.query("Firm_x != Firm_y")
    df_changedFirms = df_changedFirms[['Name', 'Firm_x', 'Firm_y']].fillna('')
    df_changedFirms = df_changedFirms.rename(columns={"Firm_x": "Old firm", "Firm_y": "New firm"}).reset_index(drop=True)
    df_changedFirms.index += 1
    return df_changedFirms

def get_lapsed_df(df_diffs: pd.DataFrame):
    df_lapsedAttorneys = df_diffs.query("NameExist == 'left_only'")
    return df_lapsedAttorneys

def name_rank_df(df: pd.DataFrame, num: int) -> pd.DataFrame:
    """Make a dataframe of <num> rows ranked by name length"""
    df['Length'] = df['Name'].apply(lambda col: len(col))
    df.sort_values(by='Length', ascending=False, inplace=True)
    df.reset_index(inplace=True)
    df.index += 1
    return df.head(num)

def filter_attorneys(df: pd.DataFrame, pat: bool, tm: bool) -> pd.DataFrame:
    """Filter attorneys based on registration type"""
    if pat:
        filter = df['Registered as'].str.contains('Patents')
        df = df[filter]
    if tm:
        filter = df['Registered as'].str.contains('Trade marks')
        df = df[filter]
    return df

def consolidate_firms(df: pd.DataFrame) -> pd.DataFrame:
    """Apply consolidation rules to account for variation in firm spelling"""
    
    #TODO Acronym detection algorithm?
    # Manual consolidation dictionary
    di = {' and ':' & ', 
          'Intellectual Property Office of NZ' : 'IPONZ',
          'Intellectual Property Office of New Zealand' : 'IPONZ',
          'GRIFFITH HACK' : 'Griffith Hack',
          'WRAYS' : 'Wrays',
          'WALLINGTON-DUMMER' : 'Wallington-Dummer',
          'ORIGIN' : 'Origin',
          'Origin IP' : 'Origin',
          'MADDERNS' : 'Madderns'
          }

    for old, new in di.items():
        df['Firm'] = df['Firm'].str.replace(old, new)

    #TODO Improve the suffix elimination to better account for variations
    for suffix in [' Limited', ' Ltd', ' LIMITED', ' LTD', ' Pty', ' Pte', ' PTY',
                   ' Patent & Trade Mark Attorneys', 
                   ' Patent & Trade Marks Attorneys',
                   ' Patent & Trade marks attorneys',
                   ' Patent & Trademark Attorneys',
                   ' Patent & Trademark Attorney',
                   ','
                   ]:
        df['Firm'] = df['Firm'].str.removesuffix(suffix)
        #df['Firm'] = df['Firm'].str.removesuffix(suffix.upper())

    # Reformat firms listed in all uppercase
    mask = df['Firm'].str.isupper() & df['Firm'].str.contains(' ')
    df.loc[mask, 'Firm'] = df['Firm'].str.title()
    for partial_acronym in ['DLA ', 'HWL ', ' IP']:
        df['Firm'] = df['Firm'].str.replace(partial_acronym.title(), partial_acronym)

    # Label blank entry as no firm
    df['Firm'] = df['Firm'].replace(r'^\s*$', '<No firm>', regex=True)

    return df

def firm_rank_df(df: pd.DataFrame, num: int, raw: bool) -> pd.DataFrame:
    """Make a dataframe of <num> rows representing firms ranked by attorney count"""
    
    if not raw:
        df = consolidate_firms(df)
    
    firm_df = df['Firm'].value_counts().to_frame()
    firm_df.reset_index(inplace=True)
    firm_df.index += 1
    firm_df = firm_df.rename(columns={'count': 'Attorneys'})

    return firm_df.head(num)

def attorneys_df_to_lines(attorneys_df: pd.DataFrame) -> list[str]:
    """Convert a dataframe of attorneys to a list of strings to act as lines for display."""
    return [f"{attorney.Name}." if attorney.Firm == '' else f"{attorney.Name} of {attorney.Firm}." for attorney in attorneys_df.itertuples()]

def check_already_scraped(dirPath: Path) -> bool:
    filepaths = get_csv_filepaths(dirPath)
    latestFilepath = filepaths[-1]
    date = str(datetime.date.today())
    return date == latestFilepath.stem