import requests
import logging
import json
import sys
import datetime
from retrying import retry
from fcreplay import get as fcreplayget
from bs4 import BeautifulSoup

with open("config.json", "r") as json_data_file:
    config = json.load(json_data_file)

# Setup Log
logging.basicConfig(
        format='%(asctime)s %(levelname)s: %(message)s',
        filename=config['logfile'],
        level=config['loglevel'],
        datefmt='%Y-%m-%d %H:%M:%S'
)

@retry(wait_random_min=5000, wait_random_max=10000, stop_max_attempt_number=3)
def get_profile(profile):
    r = requests.get(f"https://www.fightcade.com/id/{profile}")
    if r.status_code == 500:
        logging.error("500 Code, trying up to 3 times")
        raise IOError("Unable to get data")
    else:
        return r


def main(profile, challenge):
    # Check if profile exists, raise exception if it doesn't
    fcreplayget.check_for_profile(profile)

    # Get profile page
    logging.info('Getting profile page')
    r = get_profile(profile)

    table = []

    # The fightcade site has some pretty relaxed html syntax. So mangling it...
    logging.info('Getting table data')
    for line in r.text.splitlines():
        if '@sfiii3n' in line:
            line = "<tr>" + line + "</tr>"
            bs = BeautifulSoup(line, features='html.parser')
            rows = bs.findAll('tr')
            for row in rows:
                elements = row.findAll('td')
                nrow = []
                for element in elements:
                    nrow.append(element.get_text())
                table.append(nrow)

    for row in table:
        if challenge in row:
            # Dates are different
            date_old = row[0]
            date_new = datetime.datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
            row[0] = date_new.strftime('%d %b %Y %H:%M:%S')

            # Add to DB
            logging.info('Adding player replay to DB')
            status = fcreplayget.addreplay(row, player_replay=True)
            return(status)

    logging.error('Unable to find replay in player profile')
    raise LookupError


def console():
    main(sys.argv[1], sys.argv[2])

if __name__ == '__main__':
    main()