import datetime
from pathlib import Path
import pandas as pd

def get_csv_filepaths(folderPath: Path) -> list[Path]:
    """Returns a list of filepaths to all the csv files in time order."""
    # ISO naming format means default sort will time-order
    return sorted(list(folderPath.glob('*.csv')))

def get_latest_csvs(csvFilepaths: list[Path], num: int) -> list[Path]:
    """Returns the latest <num> filepaths based on their ISO dated name."""
    csvFilepaths.sort()
    latest_csv_filepaths = [csvFilepaths[-i] for i in range(1, num+1)]
    return latest_csv_filepaths

def validate_date(date: str) -> None:
    """Raises an error if <date> is not in ISO format."""
    try:
        datetime.date.fromisoformat(date)
    except ValueError:
        raise ValueError("Incorrect date format, should be YYYY-MM-DD")

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

def create_dataframes(date1_path: Path, date2_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Returns a pair of dataframes created using a pair of filepaths to csvs."""
    #Read the CSV data into dataframes
    df_date1 = pd.read_csv(date1_path, dtype='string')
    df_date2 = pd.read_csv(date2_path, dtype='string')

    # Replace missing values with empty strings for comparison purposes
    df_date1.fillna('')
    df_date2.fillna('')

    #diff = df_date2.compare(df_date1, align_axis=1)

    # Reset the index
    df_date2 = df_date2.reset_index()

    return df_date1, df_date2

def get_diffs(df_date1: pd.DataFrame, df_date2: pd.DataFrame) -> tuple[pd.DataFrame,pd.DataFrame]:
    """Return dataframes showing all the differences in data between two input dataframes."""
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

def compare_csvs(date1_path: Path, date2_path: Path) -> tuple[pd.DataFrame,pd.DataFrame]:
    """Return a dataframe with data of all the new attorneys, and another with those who changed firms."""
    # Data comparison steps
    (df_date1, df_date2) = create_dataframes(date1_path, date2_path)
    (df_left, df_right) = get_diffs(df_date1, df_date2)
    
    # Find which names are new
    df_names = pd.merge(df_left, df_right, on='Name', how="outer", indicator="NameExist")

    df_newAttorneys = df_names.query("NameExist == 'right_only'")
    df_lapsedAttorneys = df_names.query("NameExist == 'left_only'")
    df_changedDetails = df_names.query("NameExist == 'both'")

    df_changedFirms = df_changedDetails.query("Firm_x != Firm_y")

    # TODO: Consider doing a comparison of registrations and capturing those going from single to dual registered

    # Prep the needed data, replace missing values with empty strings to assist comparisons later on
    df_newAttorneys = df_newAttorneys[['Name', 'Firm_y', 'Registered as_y']].fillna('')
    df_changedFirms = df_changedFirms[['Name', 'Firm_x', 'Firm_y']].fillna('')

    # Reformat for readability
    df_newAttorneys = df_newAttorneys.rename(columns={"Firm_y": "Firm", "Registered as_y": "Registered as"}).reset_index(drop=True)
    df_changedFirms = df_changedFirms.rename(columns={"Firm_x": "Old firm", "Firm_y": "New firm"}).reset_index(drop=True)
    df_newAttorneys.index += 1
    df_changedFirms.index += 1

    return df_newAttorneys, df_changedFirms