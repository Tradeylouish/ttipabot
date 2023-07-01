# TTIPABot

This is a webscraper for the public register maintained by the Trans-Tasman Intellectual Property Attorneys Board (TTIPAB), which contains data on registered patent and trade mark attorneys in Australia and New Zealand.

The public register has a [search function](https://www.ttipattorney.gov.au/for-clients/how-to-engage-an-attorney/find-an-ip-attorney-or-firm), but it provides no way to view the full register on one page or download the full contents.

However, the backend which serves the data will return the full list as HTML if the correct number of results is requested. 

TTIPABot makes this request, parses the HTML, and writes the data to a csv file.

The data can then be analysed, including comparisons to previous scrapes to identify new registrations and attorney movement.
