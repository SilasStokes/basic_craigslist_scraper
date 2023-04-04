# Selenium imports
import selenium.webdriver as webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By

# DB imports

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
from models import get_engine, Config, Base, get_db, Session

# twilio imports
from twilio.rest import Client

# setting up program variables:

parser = argparse.ArgumentParser()
parser.add_argument('--config', default='./configs/myconfig.json',
                    help='pass the file path to your keyfile')

cl_args = parser.parse_args()


try:
    with open(cl_args.config) as json_file:
        config = Config(**json.load(json_file))
except Exception as exc:
    print(
        f'ERROR: check config file - something is broken.{Exception=} {exc=}. Exiting...')
    exit()

# # setting up database
# Base.metadata.create_all(engine)
name = cl_args.config.split(sep='/')[-1].removesuffix('.json')
db = get_db(f'{name}')
engine = get_engine(user=config.db_user,
                    password=config.db_password, echo=False)
db.metadata.create_all(engine)
error_count = 0

def browser_setup():
    user_agent = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/109.0'
    # firefox_driver_path = f'{os.getcwd()}/drivers/geckodriver'
    # firefox_options = webdriver.FirefoxOptions()
    # firefox_options.binary_location = '/usr/bin/firefox'
    # firefox_service = Service(firefox_driver_path)
    firefox_option = Options()
    firefox_option.add_argument('-headless')
    firefox_option.set_preference('general.useragent.override', user_agent)
    browser = webdriver.Firefox(options=firefox_option)
    # browser = webdriver.Firefox(service=firefox_service, options=firefox_option)
    # browser.implicitly_wait(1)  # my computer slow asf
    return browser




def translate_html_elements(timestamp: str, browser):
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

        result = db(link=link, title=title, cl_id=cl_id, screenshot_path='',
                    time_posted=posted_time, location=location, time_scraped=timestamp)
        listings.append(result)
    return listings


def scrape(url: str, timestamp: str):
    global error_count
    browser = browser_setup()
    browser.get(url)
    num_listings = 0

    # get all list items
    with Session(engine) as session:
        try:
            listings = translate_html_elements(timestamp, browser=browser)
        except Exception as exc:
            browser.quit()
            error_count += 1
            send_error_alert(
                f'ERROR: {exc=}\nScript will try {3-error_count} more times and then shutdown.')
            if error_count == 3:
                send_error_alert(
                    f'ERROR: {exc=} - Ask silas to restart the script.')
                exit()
            return
        browser.quit()

        num_listings = len(listings)
        for listing in listings:
            if not session.query(db).filter(db.cl_id == listing.cl_id).first():
                # remove this monstrosity and reaplce with the ** operator,
                # entry = db(cl_id=listing.cl_id, link=listing.link, title=listing.title, screenshot_path=listing.screenshot_path,
                #                          time_posted=listing.time_posted, location=listing.location, time_scraped=listing.time_scraped)
                session.add(listing)
                # session.add(entry)
                # session.add(db_listing_entry(**dict(listing)))

        session.commit()

    return num_listings


def welcome_message():
    print(f'''
    Welcome to the craigslist free alert searcher. 
    Every 3 minutes this script will query cl for free items and then print the new items to the terminal.
    cheers!
    ''')


def send_email_alert(alert ):
    msg = EmailMessage()
    msg['Subject'] = f'cl item alert'
    msg['From'] = config.src_email
    msg['To'] = config.dst_emails
    msg.set_content(alert.to_json())

    ssl_context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ssl_context) as server:
        server.login(config.src_email, config.email_key)
        server.send_message(msg)


def send_error_alert(error: str):
    client = Client(config.twilio_account_sid, config.twilio_auth_token)
    client.messages.create(
        body=error,
        # body=message_body,
        from_=config.src_phone_number,
        to=config.dst_phone_numbers
    )


def send_sms_alert(alert):
    client = Client(config.twilio_account_sid, config.twilio_auth_token)
    message_body = f'title: {alert.title}\nscraped: {alert.time_scraped}\nposted: {alert.time_posted}\nlocation:{alert.location}\n{alert.link}'
    print(message_body)
    client.messages.create(
        body=message_body,
        # body=message_body,
        from_=config.src_phone_number,
        to=config.dst_phone_numbers
    )


def send_alert(alert):
    # if bool(config['send_email_alerts']):
    #     send_email_alert(alert)
    if bool(config.send_sms_alerts):
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
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for i, url in enumerate(config.urls):
            # returns the number of new listings
            scrape(url, timestamp)
            if intial_loop:
                continue

            with Session(engine) as session:
                listings = session.query(db).filter(
                    db.time_scraped == timestamp)
                for i,  listing in enumerate(listings):
                    print(f'{i}. {listing.title} : {listing.link}')
                    send_alert(listing)

            # sleep before we get the next url result
            if i != len(config.urls) - 1:
                sleep_random(5, 15)

        intial_loop = False
        # sleep between 3 and 6 minutes
        sleep_random(30, 60)


if __name__ == "__main__":
    main()
