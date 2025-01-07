import ttipabot as tt
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

# Define some options shared between commands
dates_option = click.option('-d', '--dates', nargs=2, default=tt.get_dates(num=2, oldest=False, changesOnly=True), help='Dates to compare, in format: YY-MM-DD YY-MM-DD')
date_option = click.option('-d', '--date', default=tt.get_latest_date(), help='Date to do ranking on.')
markdown_option = click.option('--markdown / --no-markdown', default=True, show_default=True)
pat_option = click.option('--pat', is_flag=True, show_default=True, default=False, help='Filter by patent attorneys.')
tm_option = click.option('--tm', is_flag=True, show_default=True, default=False, help='Filter by TM attorneys.')
num_option = click.option('-n', '--num', default=10, help='Number of places in ranking.')

@cli.command()
@dates_option
@markdown_option
@pat_option
@tm_option 
def regos(dates, markdown, pat, tm):
    """Show new attorney registrations."""
    dates = sorted(dates)
    output = tt.compare_data(dates, pat, tm, mode='registrations', markdown=markdown)
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
    output = tt.compare_data(dates, pat, tm, mode='movements')
    click.echo(f"The following {tt.describe_attorney_filter(pat, tm)} attorneys changed firms between {dates[0]} and {dates[1]}:\n{output}")
    
@cli.command()
@dates_option
@pat_option
@tm_option
def lapses(dates, pat, tm):
    """Show attorneys that let their registration lapse."""
    dates = sorted(dates)
    output = tt.compare_data(dates, pat, tm, mode='lapses')
    click.echo(f"The following {tt.describe_attorney_filter(pat, tm)} attorneys had their registrations lapse between {dates[0]} and {dates[1]}:\n{output}")

@cli.command()
@date_option
@num_option
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
@click.option('-n', '--num', default=tt.count_dates(), help='number of recent scraped dates to print')
@click.option('--oldest/--newest', default=False, show_default=True)
def dates(num, oldest):
    """Show dates with scraped data available."""
    click.echo(f"Listing {num} {"oldest" if oldest else "newest"} dates out of {tt.count_dates()} dates available:")
    dates = tt.get_dates(num, oldest)
    # Order the dates so the newest/oldest one is easily visible at the bottom
    for date in reversed(dates) if oldest else dates:
        click.echo(date)

@cli.command()
@date_option
@num_option
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