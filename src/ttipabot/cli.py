from ttipabot import app as tt
import click

# Thin wrappers for cli commands
@click.group()
def cli():
    """Command line tool for interacting with the TTIPA register."""
    pass
        
@cli.command()
@click.option('--compare', is_flag=True, show_default=True, default=False, help='Run compare command after scrape')
@click.option('--chant', is_flag=True, show_default=True, default=False, help='Run compare command with the chant flag')
@click.option('--ranknames', is_flag=True, show_default=True, default=False, help='Run ranknames command after scrape')
def scrape(compare, chant, ranknames):
    """Scrape the TTIPA register."""
    tt.scrape_register()
    # Optionally call the other commands using the scrape just performed
    if chant: compare = True
    if compare: tt.compare_data(t.get_latest_dates(num=2), chant)
    if ranknames: tt.rank_names(date=tt.get_latest_dates(num=1)[0], num=10)

@cli.command()
@click.option('--dates', nargs=2, default=tt.get_latest_dates(num=2), help='dates to compare, in format: YY-MM-DD YY-MM-DD')
@click.option('--chant', is_flag=True, show_default=True, default=False, help='Sardaukar chant for any new attorneys. Or a quote.')
def compare(dates, chant):
    """Compare previously scraped data from two different dates."""
    tt.compare_data(dates, chant)

@cli.command()
@click.option('--date', default=tt.get_latest_dates(num=1)[0], help='date to rank name lengths')
@click.option('--num', default=10, help='number of names in top ranking')
@click.option('--chant', is_flag=True, show_default=True, default=False, help='Sardaukar chant for the attorneys with the longest names.')
def names(date, num, chant):
    """Rank the longest names on the register."""
    tt.rank_names(date, num, chant)

@cli.command()
@click.option('--num', default=365, help='number of recent scraped dates to print')
def dates(num):
    """Print the dates of previous scrapes."""
    tt.print_dates(num)