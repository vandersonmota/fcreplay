import requests
import sqlite3
import logging
import json
import get as fcreplayget
from bs4 import BeautifulSoup

with open("config.json") as json_data_file:
    config = json.load(json_data_file)

# Setup Log
logging.basicConfig(
        format='%(asctime)s %(levelname)s: %(message)s',
        filename=config['logfile'],
        level=config['loglevel'],
        datefmt='%Y-%m-%d %H:%M:%S'
)

def main(profile, challenge):
    fcreplayget.check_for_profile(profile)

    # Get profile page
    logging.info('Getting profile page')
    r = requests.get(f"https://www.fightcade.com/id/{profile}")

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
            # Add to DB
            logging.info('Adding player replay to DB')
            fcreplayget.addreplay(row, player_replay=True)
            return(True)

    logging.error('Unable to find replay in player profile')
    raise LookupError


if __name__ == '__main__':
    main()