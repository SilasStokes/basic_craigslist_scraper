import os
import time
import datetime
import selenium.webdriver as webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support.ui import Select
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import ElementNotInteractableException
# from bs4 import BeautifulSoup
# import pandas as pd

# DB imports
from sqlalchemy import Column, Float, String, DateTime
from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy import select


Base = declarative_base()

class DB_Listing(Base):
    '''
    Google python metaclass to read about the declarative_base pattern
    __init__(self) is in Base class Listing inherts from.
    '''
    __tablename__ = 'listings'
    id = Column(String, primary_key=True)
    title = Column(String)
    image_path = Column(String)
    created = Column(DateTime)
    link = Column(String)
    price = Column(Float)

    def __repr__(self):
        return f'{self.title=} {self.price=} {self.link=}'



# :memory: allows the db to be held in ram -- for testing purposes.
engine = create_engine("sqlite+pysqlite:///:memory:", echo = False, future = True)
Base.metadata.create_all(engine)

# browser setup
user_agent = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/109.0' # swap to fake user agent?
firefox_driver_path = f'{os.getcwd()}/geckodriver'
firefox_options = webdriver.FirefoxOptions()
firefox_options.binary_location = '/usr/bin/firefox'
firefox_service = Service(firefox_driver_path)
firefox_option = Options()
firefox_option.set_preference('general.useragent.override', user_agent)
browser = webdriver.Firefox(service=firefox_service, options=firefox_option)
browser.implicitly_wait(15) # my computer slow asf

url = 'https://seattle.craigslist.org'
free_items_url = f'{url}/search/zip#search=1~gallery~0~0'
all_forsale_url = f'{url}/search/sss#search=1~gallery~0~0'
browser.get(free_items_url)
# browser.get(all_forsale_url)

time.sleep(1.5)

def translate_html_elements():
    listings = []
    free_elements = browser.find_elements(by=By.CLASS_NAME, value='cl-search-result')
    for el in free_elements:
        a_tag = el.find_element(by=By.CLASS_NAME, value='titlestring')
        title = a_tag.text
        link = a_tag.get_attribute('href')
        id = link.split(sep='/')[-1].removesuffix('.html')
        result = {
            'link': link,
            'title': title,
            'id': id
        }
        listings.append(result)
    return listings


def scrape():
    browser.refresh()
    new_listings = []

    # get all list items
    listings = translate_html_elements()

    with Session(engine) as session:
        for listing in listings:
            # print(f'Seeing if link already in db {link=}')
            stmt = select(DB_Listing).where(DB_Listing.link.in_([listing.get('link', '')]))
            res = session.scalars(stmt).all()
            if not res:
                db_listing = DB_Listing(
                    id = listing.get('id', ''),
                    title = listing.get('title', ''),
                    image_path = 'None', #f'/home/si/code/craigslist/craigslist_venv/screenshots/{title}_{timestamp}.png',
                    created = datetime.datetime.now(), # maybe this should be pulled frm the ad itself
                    # created = datetime.datetime(), # maybe this should be pulled frm the ad itself
                    link = listing.get('link', ''),
                    price = 0.0,
                )
                new_listings.append(listing)
                session.add(db_listing)
        session.commit()
    return new_listings

def main():
    print(f'''
    Welcome to the craigslist free alert searcher. Every 3 minutes this script will query cl for free items and then print the new items to the terminal.
    cheers!
    ''')
    while True:
        # get results
        new_listings = scrape()

        # set alert
        if not new_listings:
            print(f'No new listings...')
        else:
            print(f'New listings: ')
            for i, listing in enumerate( new_listings):
                print(f'\t{i}. {listing}')


        # sleep 3 minutes
        print('sleeping for 3 minutes...')
        for i in range(0, 3*60):
            print(f'{i}... ')
            time.sleep(1)

if __name__ == "__main__":
    main()