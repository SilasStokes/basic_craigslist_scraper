# Selenium imports
import selenium.webdriver as webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By

# DB imports
# from sqlalchemy import Column, Float, String, DateTime
# from sqlalchemy.orm import declarative_base
# from sqlalchemy import create_engine
# from sqlalchemy.orm import Session
# from sqlalchemy import select

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
import argparse

# custom imports:
from models import Craigslist_Result_Card

# twilio imports
from twilio.rest import Client

# setting up program variables:
config = {}
parser = argparse.ArgumentParser()
parser.add_argument('--config-path', default='myconfig.json',
                    help='pass the file path to your keyfile')

cl_args = parser.parse_args()

try:
    with open(cl_args.config_path) as json_file:
        config = json.load(json_file)
    assert 'craigslist_urls' in config
    assert 'send_email_alerts' in config
    assert 'send_sms_alerts' in config

    if bool(config['send_email_alerts']):
        assert 'dst_emails' in config
        assert 'src_email' in config
        assert 'email_key' in config
    if bool(config['send_sms_alerts']):
        assert 'src_phone_number' in config
        assert 'dst_phone_numbers' in config
except Exception as exc:
    print(
        f'ERROR: check config file - something is broken.{Exception=} {exc=}. Exiting...')
    exit()


# # setting up database
# Base = declarative_base()
# class DB_Listing(Base):
#     '''
#     Google python metaclass to read about the declarative_base pattern
#     __init__(self) is in Base class Listing inherts from.
#     '''
#     __tablename__ = 'listings'
#     id = Column(String, primary_key=True)
#     title = Column(String)
#     image_path = Column(String)
#     created = Column(DateTime)
#     link = Column(String)
#     price = Column(Float)

#     def __repr__(self):
#         return f'{self.title=} {self.price=} {self.link=}'

#     # if we wanted to init DB_Listing with a dictionary we could do it here.
#     # Research may be done to see if we have call the base class's __init__ method as well.
#     # def __init__(self):
#     #     ...

# # :memory: allows the db to be held in ram -- for testing purposes.
# engine = create_engine("sqlite+pysqlite:///:memory:", echo = False, future = True)
# Base.metadata.create_all(engine)


# browser setup
# swap to fake user agent?
user_agent = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/109.0'
# change this to use the pathlib
# dir_path = os.path.dirname(os.path.realpath(__file__))
firefox_driver_path = f'{os.getcwd()}/drivers/geckodriver'
# firefox_options = webdriver.FirefoxOptions()
# firefox_options.binary_location = '/usr/bin/firefox'
# firefox_service = Service(firefox_driver_path)
firefox_option = Options()
firefox_option.add_argument('-headless')
firefox_option.set_preference('general.useragent.override', user_agent)
browser = webdriver.Firefox(options=firefox_option)
# browser = webdriver.Firefox(service=firefox_service, options=firefox_option)
browser.implicitly_wait(1)  # my computer slow asf
browser.get('https://google.com')


def translate_html_elements():
    listings = []
    free_elements = browser.find_elements(
        by=By.CLASS_NAME, value='cl-search-result')
    for el in free_elements:
        a_tag = el.find_element(by=By.CLASS_NAME, value='titlestring')
        title = a_tag.text
        link = a_tag.get_attribute('href')
        id = link.split(sep='/')[-1].removesuffix('.html')
        result = Craigslist_Result_Card(
            link=link, title=title, id=id, screenshot_path='')
        listings.append(result)
    return listings


def scrape(url):
    browser.refresh()
    browser.get(url)
    new_listings = []

    # get all list items
    listings = translate_html_elements()

    # swap this to a database after benchmarking
    existing_records = []
    if os.path.isfile('database.json'):
        with open('database.json', 'r', ) as db:
            js = json.load(db)
            for record in js:
                existing_records.append(Craigslist_Result_Card(**record))

    for listing in listings:
        if listing not in existing_records:
            new_listings.append(listing)
            existing_records.append(listing)

    with open('database.json', 'w') as db:
        json.dump(Craigslist_Result_Card.schema().dump(
            existing_records, many=True), db)

    return new_listings


def welcome_message():
    print(f'''
    Welcome to the craigslist free alert searcher. 
    Every 3 minutes this script will query cl for free items and then print the new items to the terminal.
    cheers!
    ''')


def send_email_alert(alert: Craigslist_Result_Card):
    msg = EmailMessage()
    msg['Subject'] = f'cl item alert'
    msg['From'] = config['src_email']
    msg['To'] = config['dst_emails']
    msg.set_content(alert.to_json())

    ssl_context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ssl_context) as server:
        server.login(config['src_email'], config['email_key'])
        server.send_message(msg)


def send_sms_alert(alert: Craigslist_Result_Card):
    # print('sending sms..')
    client = Client(config['twilio_account_sid'], config['twilio_auth_token'])

    message = client.messages.create(
        body=alert.link,
        from_=config['src_phone_number'],
        to=config['dst_phone_numbers'][0]
    )


def send_alert(alert: Craigslist_Result_Card):
    #    if bool(config['send_email_alerts']):
    #        send_email_alert(alert)
    if bool(config['send_sms_alerts']):
        send_sms_alert(alert)


def sleep_random(lval, rval):
    seconds = random.randint(lval, rval)
    timestamp = datetime.datetime.now()  # .strftime('%Y-%m-%d %H:%M:%S')
    next_iteration = timestamp + datetime.timedelta(seconds=seconds)
    print(f"{timestamp.strftime('%Y-%m-%d %H:%M:%S')}: sleeping for {seconds//60} minutes and {seconds%60} seconds..., next request at {next_iteration.strftime('%Y-%m-%d %H:%M:%S')}")
    time.sleep(seconds)


def main():
    # begin scrape loop:
    intial_loop = True
    while True:
        # get results
        for url in config['craigslist_urls']:
            new_listings = scrape(url)

            # if there's listings, send them whichever way is declared in config.json
            if new_listings:
                # build the alert content string
                alert_content = ""
                for i, listing in enumerate(new_listings):
                    title = listing.title
                    link = listing.link
                    alert_content = alert_content + f'{i}. {title} : {link}\n'

                    if not intial_loop:
                        send_alert(listing)
                print(alert_content)
            # sleep before we get the next url result
            sleep_random(5, 15)

        intial_loop = False
        # sleep between 3 and 6 minutes
        sleep_random(180, 360)


if __name__ == "__main__":
    main()
