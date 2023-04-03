# Selenium imports
import selenium.webdriver as webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By

# DB imports
# from sqlalchemy import Column, Float, String, DateTime
# from sqlalchemy.orm import declarative_base
# from sqlalchemy import create_engine
from sqlalchemy.orm import Session
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
from models import Craigslist_Result_Card, engine, db_listing_entry, Config, Base

# twilio imports
from twilio.rest import Client

# setting up program variables:
config = {}
parser = argparse.ArgumentParser()
parser.add_argument('--config-path', default='./configs/myconfig.json',
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
Base.metadata.create_all(engine)


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
# firefox_option.add_argument('-headless')
firefox_option.set_preference('general.useragent.override', user_agent)
browser = webdriver.Firefox(options=firefox_option)
# browser = webdriver.Firefox(service=firefox_service, options=firefox_option)
browser.implicitly_wait(1)  # my computer slow asf
browser.get('https://google.com')


def translate_html_elements():
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    listings = []
    free_elements = browser.find_elements(
        by=By.CLASS_NAME, value='cl-search-result')
    for el in free_elements:
        a_tag = el.find_element(by=By.CLASS_NAME, value='titlestring')
        title = a_tag.text
        link = a_tag.get_attribute('href')
        cl_id = link.split(sep='/')[-1].removesuffix('.html')
        meta_string = el.find_element(by=By.CLASS_NAME, value='meta').text
        posted_time, location = meta_string.split(sep='·')

        result = Craigslist_Result_Card(
            link=link, title=title, cl_id=cl_id, screenshot_path='', time_posted=posted_time, location=location, time_scraped=timestamp)
        listings.append(result)
    return listings


def scrape(url):
    browser.refresh()
    browser.get(url)
    new_listings = []

    # get all list items
    listings = translate_html_elements()

    with Session(engine) as session:
        for listing in listings:
            if not session.query(db_listing_entry).filter(db_listing_entry.cl_id == listing.cl_id).first():
                new_listings.append(listing)
                # remove this monstrosity and reaplce with the ** operator,
                entry = db_listing_entry(cl_id=listing.cl_id, link=listing.link, title=listing.title, screenshot_path=listing.screenshot_path,
                                         time_posted=listing.time_posted, location=listing.location, time_scraped=listing.time_scraped)
                session.add(entry)
                # session.add(db_listing_entry(**dict(listing)))
        session.commit()

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
    client = Client(config['twilio_account_sid'], config['twilio_auth_token'])
    message_body = f'title: {alert.title}\ntimestamp: {alert.time_scraped}\nposted: {alert.time_posted}\nlocation:{alert.location}\n{alert.link}'
    print(message_body)

    client.messages.create(
        body=message_body,
        from_=config['src_phone_number'],
        to=config['dst_phone_numbers'][0]
    )


def send_alert(alert: Craigslist_Result_Card):
    if bool(config['send_email_alerts']):
        send_email_alert(alert)
    if bool(config['send_sms_alerts']):
        send_sms_alert(alert)
    pass


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
            if len(config['craigslist_urls']) > 1:
                sleep_random(5, 15)

        intial_loop = False
        # sleep between 3 and 6 minutes
        sleep_random(180, 360)


if __name__ == "__main__":
    main()
