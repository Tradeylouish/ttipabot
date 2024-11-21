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
    if compare: tt.compare_data(tt.get_dates(num=2, oldest=False), chant)
    if ranknames: tt.rank_names(tt.get_latest_date(), num=10)

@cli.command()
@click.option('--dates', nargs=2, default=tt.get_dates(num=2, oldest=False), help='dates to compare, in format: YY-MM-DD YY-MM-DD')
@click.option('--chant', is_flag=True, show_default=True, default=False, help='Sardaukar chant for any new attorneys. Or a quote.')
@click.option('--pat', is_flag=True, show_default=True, default=False, help='Only compare patent attorneys.')
@click.option('--tm', is_flag=True, show_default=True, default=False, help='Only compare TM attorneys.')
def compare(dates, chant, pat, tm):
    """Compare previously scraped data from two different dates."""
    output = tt.compare_data(dates, chant, pat, tm)
    click.echo(output)

@cli.command()
@click.option('--date', default=tt.get_latest_date(), help='date to rank name lengths')
@click.option('--num', default=10, help='number of names in top ranking')
@click.option('--chant', is_flag=True, show_default=True, default=False, help='Sardaukar chant for the attorneys with the longest names.')
def names(date, num, chant):
    """Rank the longest names on the register."""
    output = tt.rank_names(date, num, chant)
    click.echo(output)

@cli.command()
@click.option('--num', default=tt.count_dates(), help='number of recent scraped dates to print')
@click.option('--oldest', is_flag=True, show_default=True, default=False, help='list dates in reverse order')
def dates(num, oldest):
    """Print the dates of previous scrapes."""
    output = tt.list_dates(num, oldest)
    click.echo(output)

@cli.command()
@click.option('--date', default=tt.get_latest_date(), help='date to rank firms')
@click.option('--num', default=10, help='number of firms in top ranking')
@click.option('--pat', is_flag=True, show_default=True, default=False, help='Only count patent attorneys.')
@click.option('--tm', is_flag=True, show_default=True, default=False, help='Only count TM attorneys.')
@click.option('--raw', is_flag=True, show_default=True, default=False, help='Use raw firm data without consolidation.')
def firms(date, num, pat, tm, raw):
    """Print the dates of previous scrapes."""
    output = tt.rank_firms(date, num, pat, tm, raw)
    click.echo(output)