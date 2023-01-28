# Selenium imports
import selenium.webdriver as webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By

# DB imports
from sqlalchemy import Column, Float, String, DateTime
from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy import select

# email imports
import json
from email.message import EmailMessage
import smtplib
import ssl

# misc imports
import random
import os
import time
import datetime
import sys
import argparse


# setting up program variables:
config = {}
parser = argparse.ArgumentParser()
parser.add_argument('--config-path', default='config.json', help='pass the file path to your keyfile')

cl_args = parser.parse_args()

try:
    with open(cl_args.config) as json_file:
        config = json.load(json_file)
    assert 'craigslist_urls' in config
    assert 'send_email_alerts' in config
    assert 'send_sms_alerts' in config

    if bool(config['send_email_alerts']):
        assert 'dst_email' in config
        assert 'src_email' in config
        assert 'email_key' in config
    if bool(config['send_sms_alerts']):
        assert 'src_phone_number' in config
        assert 'dst_phone_numbers' in config
except:
    print(f'ERROR: check config file - something is broken, exiting...')
    exit()

# setting up database
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

def welcome_message():
    print(f'''
    Welcome to the craigslist free alert searcher. 
    Every 3 minutes this script will query cl for free items and then print the new items to the terminal.
    cheers!
    ''')

def send_email_alert(alert):
    # TODO: Set up email alert
    msg = EmailMessage()
    msg['Subject'] = f'cl item alert'
    msg['From'] = config['src_email']
    msg['To'] = config['dst_email']
    msg.set_content(alert)

    ssl_context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ssl_context) as server:
        server.login(config['dst_email'], config['email_key'])
        server.send_message(msg)

def send_sms_alert(alert):
    # TODO: Set up text alert with twilio
    ...

def send_alert(alert:str):
    if bool(config['send_email_alerts']):
        send_email_alert(alert)
    if bool(config['send_sms_alerts']):
        send_sms_alert(alert)


def main():
    # begin scrape loop:
    while True:
        # get results
        new_listings = scrape()

        # if there's listings, send them whichever way is declared in config.json
        if new_listings:
            alert_content = ""
            for i, listing in enumerate( new_listings):
                title = listing['title']
                link = listing['link']
                alert_content = alert_content + f'{i}. {title} : {link}\n'
            print(alert_content)
            send_alert(alert_content)


        # sleep between 3 and 6 minutes
        seconds = random.randint(3*60,6*60) 
        print(f'sleeping for {seconds//60} minutes and {seconds%60} seconds...')
        time.sleep(seconds)

if __name__ == "__main__":
    main()