from ttipabot import app as tt
import click

# Thin wrappers for cli commands
@click.group(chain=True)
def cli():
    """Command line tool for interacting with the TTIPA register."""
    pass
        
@cli.command()
def scrape():
    """Scrape the TTIPA register."""
    if tt.scrape_register():
        click.echo("Finished today's register scrape.")
    else:
        click.echo("Already scraped the register today.")

dates_option = click.option('--dates', nargs=2, default=tt.get_dates(num=2, oldest=False, changesOnly=True), help='dates to compare, in format: YY-MM-DD YY-MM-DD')
markdown_option = click.option('--markdown / --no-markdown', default=True, show_default=True)
pat_option = click.option('--pat', is_flag=True, show_default=True, default=False, help='Filter by patent attorneys.')
tm_option = click.option('--tm', is_flag=True, show_default=True, default=False, help='Filter by TM attorneys.')

@cli.command()
@dates_option
@markdown_option
@pat_option
@tm_option 
def registrations(dates, markdown, pat, tm):
    """Show new attorney registrations."""
    dates = sorted(dates)
    output = tt.compare_registrations(dates, markdown, pat, tm)
    click.echo(f"Congratulations to the new {tt.describe_attorney_filter(pat, tm)} attorneys registered between {dates[0]} and {dates[1]}:")
    # TODO Refactor to avoid multiple return types from compare_registrations
    if markdown:
       click.echo(output)
    else:
        for attorney in output:
            click.echo(attorney)
    
@cli.command()
@dates_option
@pat_option
@tm_option
def moves(dates, pat, tm):
    """Show movements of attorneys between firms."""
    dates = sorted(dates)
    output = tt.compare_movements(dates, pat, tm)
    click.echo(f"The following {tt.describe_attorney_filter(pat, tm)} attorneys changed firms between {dates[0]} and {dates[1]}:\n{output}")

@cli.command()
@click.option('--date', default=tt.get_latest_date(), help='date to rank name lengths')
@click.option('--num', default=10, help='number of names in top ranking')
@markdown_option
def names(date, num, markdown):
    """Rank the longest names on the register."""
    output = tt.rank_names(date, num, markdown)
    click.echo(f"The top {num} names by length as of {date} are:")
    # TODO Refactor to avoid multiple return types from rank_names
    if markdown:
       click.echo(output)
    else:
        for attorney in output:
            click.echo(attorney)

@cli.command()
@click.option('--num', default=tt.count_dates(), help='number of recent scraped dates to print')
@click.option('--oldest/--newest', default=False, show_default=True)
def dates(num, oldest):
    """Show dates with scraped data available."""
    click.echo(f"Listing {num} / {tt.count_dates()} dates available:")
    for date in tt.get_dates(num, oldest):
        click.echo(date)

@cli.command()
@click.option('--date', default=tt.get_latest_date(), help='date to rank firms')
@click.option('--num', default=10, help='number of firms in top ranking')
@pat_option
@tm_option
@click.option('--raw', is_flag=True, show_default=True, default=False, help='Use raw firm data without consolidation.')
def firms(date, num, pat, tm, raw):
    """Print the dates of previous scrapes."""
    output = tt.rank_firms(date, num, pat, tm, raw)
    click.echo(f"The biggest {num} firms by attorney count as of {date} are:\n{output}")
    
@cli.command()
def cleanup():
    """Clean up duplicate scrapes."""
    csvs_deleted = tt.cleanup()
    if csvs_deleted > 0:
        click.echo(f"Deleted {csvs_deleted} scraped csv files and mapped to earlier dates.")
    else:
        click.echo("Nothing to clean up.")