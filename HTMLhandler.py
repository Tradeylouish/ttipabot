import datetime
import csv
from bs4 import BeautifulSoup, Tag

# Read in the raw HTML
rawHTML = ""
with open("registerHTML.txt", 'r', encoding="utf-8") as f:
    rawHTML = f.read()


# Parse and extract all the data
soup = BeautifulSoup(rawHTML, 'lxml')

results = soup.find_all(class_="list-item attorney")

data = []

for result in results:
    # Skip blank name entries
    name = result.h4.contents
    if not name: continue
    name = result.h4.contents[0]

    # Check tags for registrations, convert to comma separated string
    registeredAs = []
    for tag in result.find_all(class_="ipr-tag"):
        registeredAs += tag.contents
    
    registeredAs = ", ".join(registeredAs)
    
    # Get phone numbers
    if not result.find(class_="block-1"): 
        phone = ""
    else: 
        for child in result.find(class_="block-1").children:
            if isinstance(child, Tag) and child.a:
                phone = child.a.contents[0]

    # Get emails
    if not result.find(class_="block-2"): 
        email = ""
    else: 
        for child in result.find(class_="block-2").children:
            if isinstance(child, Tag) and child.a:
                email = child.a.contents[0]

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

    data.append([name, phone, email, firm, address, registeredAs])


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



#print('longest: ' + max(names, key = len))