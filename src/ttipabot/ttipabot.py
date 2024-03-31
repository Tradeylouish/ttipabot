import logging
import datetime
import csv
from pathlib import Path
import random

import requests
import pandas as pd
from bs4 import BeautifulSoup, Tag
import click
import pygame


logger = logging.getLogger(__name__)
logging.basicConfig(filename='ttipabot.log', encoding='utf-8', format='%(asctime)s %(message)s', level=logging.DEBUG)

CSV_FOLDER = Path.cwd() / "TTIPAB register saves"

def ttipab_request(count):
    # Public API endpoint as determined by Inspect Element > Network > Requests on Google Chrome
    urlBase = "https://www.ttipattorney.gov.au//sxa/search/results/"
    urlOptions1 = "?s={21522AF6-8499-4C63-8CFA-02E2B97737BE}&itemid={8B94FE47-304A-4629-AD46-DD208EEF71AA}&sig=als&e=0&p="
    urlOptions2 = "&v=%7B2FCA44D4-EE00-43EC-BBBF-858C31387413%7D"
    url =  f"{urlBase}{urlOptions1}{count}{urlOptions2}"
    return requests.get(url, stream=True)

def get_full_register():
    
    try:
        #Do an intial ping of the register to determine the total number of results to be requested
        initialResponse = ttipab_request(1)
        #Convert JSON response to dict and extract count
        resultsCount = initialResponse.json().get("Count")
        #Request the full contents of the register
        rawHTML = ttipab_request(resultsCount).text

        logger.debug(f"Scraped {resultsCount} results from the register.")

    except Exception as ex:
        logger.error("Failed to scrape register, could be a server-side problem.", exc_info= ex)
        exit()

    # Get rid of control characters
    rawHTML = rawHTML.replace("\\r", "")
    rawHTML = rawHTML.replace("\\n", "")
    rawHTML = rawHTML.replace("\\", "")

    # Parse and extract all the data
    soup = BeautifulSoup(rawHTML, 'lxml')

    attorneys = soup.find_all(class_="list-item attorney")

    return attorneys

def get_contact_data(result, searchString):
    tag = result.find("span", string=searchString)
    if tag is None:
        return ""
    
    #Data is always in (non-whitespace) descendant string(s) of the tag that follows
    #Could be two strings for dual registrations, so comma join
    return ", ".join(tag.find_next_sibling().stripped_strings) 

def get_attorney_data(attorney):
    #Takes a soup representing an attorney
    fields = [" Attorney ", " Phone ", " Email ", " Firm ", " Address ", " Registered as"]
    return [get_contact_data(attorney, field) for field in fields]

def parse_register(attorneys):
    #Takes a list of soup objects representing attorneys
    data = [get_attorney_data(attorney) for attorney in attorneys 
            if get_contact_data(attorney, " Attorney ") != ""]

    return data

def write_to_csv(data, folderpath):
    #Print the register contents to a CSV file
    spreadsheet_name = folderpath / (str(datetime.date.today()) + '.csv')

    header = ['Name', 'Phone', 'Email', 'Firm', 'Address', 'Registered as']

    # open the file in the write mode
    with spreadsheet_name.open('w', encoding="utf-8", newline='') as f:
        writer = csv.writer(f)
        # write header to the csv file
        writer.writerow(header)
        # write data to the csv file
        writer.writerows(data)

def write_raw_html(rawHTML):
    with open("registerDump.txt", 'w', encoding="utf-8") as f:
        f.write(rawHTML)

def scrape_register():
    results = get_full_register()
    data = parse_register(results)
    write_to_csv(data, CSV_FOLDER)

def get_csv_filepaths(folderPath):
    return list(folderPath.glob('*.csv'))

def get_latest_csvs(csvFilepaths):
    # Filename format means default sort will time-order
    csvFilepaths.sort()

    # Return the last two entries
    return csvFilepaths[-2], csvFilepaths[-1]

def get_specified_csvs(csvFilepaths, dates):
    # Look for a filepath that contain the date string
    datePaths = [next((path for path in csvFilepaths if date in str(path)), None) for date in dates]

    return datePaths

def create_dataframes(date1_path, date2_path):

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

def get_diffs(df_date1, df_date2):

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

def compare_csvs(date1_path, date2_path):
    # Data comparison steps
    (df_date1, df_date2) = create_dataframes(date1_path, date2_path)
    (df_left, df_right) = get_diffs(df_date1, df_date2)
    
    # Find which names are new
    df_names = pd.merge(df_left, df_right, on='Name', how="outer", indicator="NameExist")

    df_newAttorneys = df_names.query("NameExist == 'right_only'")
    df_lapsedAttorneys = df_names.query("NameExist == 'left_only'")
    df_changedDetails = df_names.query("NameExist == 'both'")

    df_changedFirms = df_changedDetails.query("Firm_x != Firm_y")

    #TODO: Consider doing a comparison of registrations and capturing those going from single to dual registered

    # Prep the needed data, replace missing values with empty strings to assist comparisons later on
    df_newAttorneys = df_newAttorneys[['Name', 'Firm_y', 'Registered as_y']].fillna('')
    df_changedFirms = df_changedFirms[['Name', 'Firm_x', 'Firm_y']].fillna('')

    #Reformat for readability
    df_newAttorneys = df_newAttorneys.rename(columns={"Firm_y": "Firm", "Registered as_y": "Registered as"}).reset_index(drop=True)
    df_changedFirms = df_changedFirms.rename(columns={"Firm_x": "Old firm", "Firm_y": "New firm"}).reset_index(drop=True)
    df_newAttorneys.index += 1
    df_changedFirms.index += 1

    return df_newAttorneys, df_changedFirms

def get_latest_dates(num):

    csvFilepaths = get_csv_filepaths(CSV_FOLDER)

    # Filename format means default sort will time-order
    csvFilepaths.sort()

    # Create a list of strings representing the most recent dates, length equal to num argument
    dates = [Path(csvFilepaths[-i]).stem for i in range(1, num+1)]

    return dates

def rank_names(date, num):

    #print(dates)
    csvFilepaths = get_csv_filepaths(CSV_FOLDER)
    csv = get_specified_csvs(csvFilepaths, [date])[0]

    #TODO vectorise existing code above

    df = pd.read_csv(csv, dtype='string')

    # Replace missing values with empty strings for comparison purposes
    df.fillna('')

    # Sort names and reindex to show ranking
    df['Length'] = df['Name'].apply(lambda col: len(col))
    df = df.sort_values(by='Length', ascending=False)
    df.reset_index(inplace=True)
    df.index += 1
    print(f"\nThe top {num} names by length are:\n{df[['Name', 'Length']].head(num).to_markdown()}")


def compare_data(dates, chant):

    date1, date2 = dates
    # Ensure date1 is the earliest date, so later code can assume this
    FORMAT = "%Y-%m-%d"
    if datetime.datetime.strptime(date1, FORMAT) > datetime.datetime.strptime(date2, FORMAT):
        date1, date2 = date2, date1
    
    csvFilepaths = get_csv_filepaths(CSV_FOLDER)

    (csv1, csv2) = get_specified_csvs(csvFilepaths, [date1, date2])

    logger.debug(f"Comparing dates {date1} and {date2}")

    try:
        (newAttorneys, firmChanges) = compare_csvs(csv1, csv2)

        if not newAttorneys.empty: 
            print(f"\nCongratulations to the following newly registered IP attorneys:\n{newAttorneys.to_markdown()}\n")
        if not firmChanges.empty: 
            print(f"The following attorneys have recently changed firm:\n{firmChanges.to_markdown()}\n")

    except Exception as ex:
        logger.error(f"Error analysing data, possibly anomaly in register.", exc_info= ex)
        # Create empty data frame so that the random chant can proceed
        newAttorneys = pd.DataFrame([])

    # Play a Sardaukar chant if there are any new attorneys. Otherwise shorter chant with a random quote.
    if not chant: return 

    # Get a list of all the new patent attorneys by eliminating solely TM registered (will still capture blanks, in case data missing)
    patentAttorneys = [newAttorney for newAttorney in newAttorneys.itertuples() if newAttorney._3 != 'Trade marks']

    if not patentAttorneys:
        # Select a random quote
        with open('quotes.txt', 'r') as file:
            lines = [line.rstrip() for line in file]
            text = [random.choice(lines)]
        sound_file = 'sardaukar-growl.mp3'
        logger.debug(f"No new patent attorneys found, random quote is: \"{text[0]}\"")
    else:
        text = [f"{patentAttorney.Name}." if patentAttorney.Firm_y == '' else f"{patentAttorney.Name} of {patentAttorney.Firm_y}." for patentAttorney in patentAttorneys]
        sound_file = 'sardaukar-chant.mp3'
        logger.debug(f"Found {len(text)} new patent attorneys.")
    
    perform_chant(sound_file, text)

def perform_chant(sound_file, text):

    pygame.init()
    screen = pygame.display.set_mode(flags=pygame.FULLSCREEN)
    pygame.mixer.music.load(sound_file)
    # Hacky way to ensure enough chant loops to cover everyone - based on approx ratio of chant length to number of lines to fade
    playcount = int(len(text) / 8) + 1
    try:
        pygame.mixer.music.play(playcount)
        logger.debug(f"Playing {sound_file} {playcount} time(s).")
    except Exception as ex:
        logger.error(f"Error attempting to play {sound_file}, check filepaths.", exc_info= ex)

    for line in text:
        fade_text(screen, line)
    logger.debug(f"Finished showing all text.")
    
    while pygame.mixer.music.get_busy(): 

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit()

        screen.fill(pygame.Color('black'))
        pygame.display.flip()

def fade_text(screen, line):

    clock = pygame.time.Clock()
    timer = 0
    # Constants for timing adjustment, based on Dune movie intro
    WAIT_TIME = 1500
    FADEOUT_TIME = 6000
    faded_in = False

    font = pygame.font.Font('Futura Medium.otf', 50)
    orig_surf = font.render(line, True, pygame.Color('white'))
    orig_surf_rect = orig_surf.get_rect(center = (screen.get_rect().centerx, screen.get_rect().centery * 1.5))
    txt_surf = orig_surf.copy()
    # This surface is used to adjust the alpha of the txt_surf.
    alpha_surf = pygame.Surface(txt_surf.get_size(), pygame.SRCALPHA)
    alpha = 0  # The current alpha value of the surface.

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit()

        if alpha < 255 and timer>= WAIT_TIME and not faded_in:
            # Increase alpha each frame, but make sure it doesn't go above 255.
            alpha = min(alpha+10, 255)
            if alpha == 255: faded_in=True 
        elif faded_in and timer>=FADEOUT_TIME and alpha > 0:
            # Decrease alpha each frame, but make sure it doesn't go below 0.
            alpha = max(alpha-10, 0)
            if alpha == 0: return

        txt_surf = orig_surf.copy()  # Don't modify the original text surf.
        # Fill alpha_surf with this color to set its alpha value.
        alpha_surf.fill((255, 255, 255, alpha))
        # To make the text surface transparent, blit the transparent
        # alpha_surf onto it with the BLEND_RGBA_MULT flag.
        txt_surf.blit(alpha_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        screen.fill(pygame.Color('black'))
        screen.blit(txt_surf, orig_surf_rect)
        pygame.display.flip()
        timer += clock.tick(24)


# Thin wrappers for cli commands
@click.group()
def cli():
    pass
        
@cli.command()
@click.option('--compare', is_flag=True, show_default=True, default=False, help='Run compare command after scrape')
@click.option('--chant', is_flag=True, show_default=True, default=False, help='Run compare command with the chant flag')
@click.option('--ranknames', is_flag=True, show_default=True, default=False, help='Run ranknames command after scrape')
def scrape(compare, chant, ranknames):
    #scrape_register()
    # Optionally call the other commands using the scrape just performed
    if chant: compare = True
    if compare: compare_data(get_latest_dates(num=2), chant)
    if ranknames: rank_names(date=get_latest_dates(num=1)[0], num=10)

@cli.command()
@click.option('--dates', nargs=2, default=get_latest_dates(num=2), help='dates to compare, in format: \'YY-MM-DD\' \'YY-MM-DD\'')
@click.option('--chant', is_flag=True, show_default=True, default=False, help='Sardaukar chant for any new attorneys. Or a quote.')
def compare(dates, chant):
    compare_data(dates, chant)

@cli.command()
@click.option('--date', default=get_latest_dates(num=1)[0], help='date to rank name lengths')
@click.option('--num', default=10, help='number of names in top ranking')
def ranknames(date, num):
    rank_names(date, num)

if __name__ == '__main__':
    cli()