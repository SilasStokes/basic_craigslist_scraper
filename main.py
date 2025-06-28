# Selenium imports
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# email imports
import json
from email.message import EmailMessage
import smtplib
import ssl

# discord imports
import requests

# misc imports
import random
import os
import time
import datetime
import argparse

from sqlalchemy import case, func, or_, select
from sqlalchemy.dialects import postgresql

# custom imports:
from models import get_engine, Config, Base, get_db, Session
from prettyPrint import printError, printInfo, printSuccess, welcome_message

# twilio imports
from twilio.rest import Client

# setting up program variables:

parser = argparse.ArgumentParser()
parser.add_argument('-c', '--config', default='./config/config.json',
                    help='pass the file path to your config file. Defaults to ./config/config.json. there\'s an example config file in ./config/example_config.json')

cl_args = parser.parse_args()


try:
    with open(cl_args.config) as json_file:
        config = Config(**json.load(json_file))
except Exception as exc:
    printError(
        f'check config file - something is broken.{Exception=} {exc=}. Exiting...')
    exit()

# setting up database
# Base.metadata.create_all(engine)
name = cl_args.config.split(sep='/')[-1].removesuffix('.json')
db = get_db(f'{name}')
engine = get_engine(user=config.db_user,
                    password=config.db_password, echo=False)
db.metadata.create_all(engine)
error_count = 0


def browser_setup():
    firefox_option = Options()
    firefox_option.add_argument('--headless')
    browser = webdriver.Firefox(options=firefox_option)
    browser.implicitly_wait(1)  # my computer slow asf
    return browser


def translate_html_elements(timestamp: str, browser):
    listings = []
    delay = 5  # seconds
    beforePageLoad = datetime.datetime.now()
    printInfo(beforePageLoad.strftime("%H:%M:%S"), " - Starting page load ")
    try:
        WebDriverWait(browser, delay).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'cl-search-result')))
        pass
    except TimeoutException:
        pass

    afterPageLoad = datetime.datetime.now()
    delta = afterPageLoad - beforePageLoad
    printInfo(afterPageLoad.strftime("%H:%M:%S"),
              " - Page loaded, took ", delta.seconds, 's')

    free_elements = browser.find_elements(
        by=By.CLASS_NAME, value='cl-search-result')
    for el in free_elements:
        a_tag = el.find_element(By.CLASS_NAME, 'posting-title')
        title = a_tag.text
        link = a_tag.get_attribute('href')
        cl_id = link.split(sep='/')[-1].removesuffix('.html')
        meta_string = el.find_element(by=By.CLASS_NAME, value='meta').text
        posted_time, location = meta_string.split(sep='\n')

        result = db(link=link, title=title, cl_id=cl_id,
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
        items = 0
        for listing in listings:
            qry = select(db).where(db.cl_id == listing.cl_id)
            if not session.scalars(qry).first():
            # if not session.query(db).filter(db.cl_id == listing.cl_id).first():
                printInfo('DB - adding new listing: ', listing, '\n')
                items += 1
                session.add(listing)

        if (items > 0):
            printInfo(f'Commiting {items} items to db...')
            session.commit()
            printSuccess('Commit successful')
        else:
            printInfo('Nothing to commit')

    return num_listings

def send_discord_alert(alert):
    if not config.discord_webhook_url:
        printError("Discord webhook URL not set in config.")
        return
    message_body = (
        f"@here\n"
        f"**Craigslist Alert**\n"
        f"**Title:** {alert.title}\n"
        f"**Scraped:** {alert.time_scraped}\n"
        f"**Posted:** {alert.time_posted}\n"
        f"**Location:** {alert.location}\n"
        f"{alert.link}"
    )
    data = {"content": message_body}
    try:
        response = requests.post(config.discord_webhook_url, json=data)
        if response.status_code != 204 and response.status_code != 200:
            printError(f"Discord webhook failed: {response.status_code} {response.text}")
    except Exception as exc:
        printError(f"Exception sending Discord webhook: {exc}")

def send_email_alert(alert):
    msg = EmailMessage()
    msg['Subject'] = f'cl item alert'
    msg['From'] = config.src_email
    msg['To'] = config.dst_emails
    message_body = f'title: {alert.title}\nscraped: {alert.time_scraped}\nposted: {alert.time_posted}\nlocation:{alert.location}\n{alert.link}'
    msg.set_content(message_body)

    ssl_context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ssl_context) as server:
        server.login(config.src_email, config.email_key)
        server.send_message(msg)


def send_error_alert(error: str):
    printError(error)
    client = Client(config.twilio_account_sid,
                    config.twilio_auth_token)
    client.messages.create(
        body=error,
        from_=config.src_phone_number,
        to=config.dst_phone_numbers
    )

def send_sms(msg: str):
    printInfo('Sending: ', msg)
    client = Client(config.twilio_account_sid,
                    config.twilio_auth_token)
    client.messages.create(
        body=msg,
        from_=config.src_phone_number,
        to=config.dst_phone_numbers
    )

def text_db_row(alert):
    message_body = f'title: {alert.title}\nscraped: {alert.time_scraped}\nposted: {alert.time_posted}\nlocation:{alert.location}\n{alert.link}'
    send_sms(message_body)

# alert is a db row object
def send_alert(alert):
    # Email (if enabled) 
    # TODO - fix email alerts
    # if getattr(config, "send_email_alerts", False):
    #     send_email_alert(alert)
    # SMS (if enabled)
    if getattr(config, "send_sms_alerts", False):
        text_db_row(alert)
    # Discord (if enabled)
    if getattr(config, "send_discord_alerts", False):
        send_discord_alert(alert)


def sleep_random(lval, rval):
    seconds = random.randint(lval, rval)
    next_iteration = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
    printInfo(
        f"{datetime.datetime.now().strftime('%H:%M:%S')} - Sleeping for {seconds//60} minutes and {seconds%60} seconds...")
    printInfo(
        f"{datetime.datetime.now().strftime('%H:%M:%S')} - Next request at {next_iteration.strftime('%H:%M:%S')}")
    time.sleep(seconds)


def main():
    welcome_message()
    db_query_filters = [db.title.regexp_match(f'\\b({word})\\b', 'ix') for word in config.filters]
    initial_loop = True
    while True:
        # get results
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for i, url in enumerate(config.urls):

            # returns the number of new listings
            scrape(url, timestamp)
            if initial_loop:
                continue

            # query the database for new listings and send alerts
            with Session(engine) as session:
                qry = select(db).where(db.time_scraped == timestamp, ~or_(*db_query_filters))
                listings = list(session.scalars(qry))
                for i, listing in enumerate(listings):
                    printInfo(f'{i}. {listing.title} : {listing.link}')
                    send_alert(listing)

            # sleep between 5 and 15 seconds between config urls
            if i != len(config.urls) - 1:
                sleep_random(5, 15)

        initial_loop = False
        # sleep between 45 and 90 seconds between major cycles
        sleep_random(45, 90)


if __name__ == "__main__":
    main()
