# basic_craigslist_scraper

Goal of this repo is to flesh out what it takes to scrape craigslist before I port the [craigslist python package](https://github.com/juliomalegria/python-craigslist) to use selenium instead of requests due to craigslist blocking requests that don't come from a browser with javascript enabled, [documented here](https://github.com/juliomalegria/python-craigslist/issues/116)

To install the python packages use `pip install -r requirements.txt`.

goals:
1. write a script that can pull from craigslist 24/7 without bot detection. 
2. send me alerts via email or text when a new ad I want to see becomes available.
3. create the program such that it's usable by others with little to no code set up. 
4. have the script alert me if it stops running

# To set up email:
suprisingly simple with gmail.
1. go to the account you want emails to be sent from, (click the 9 squares on the top right of google -> top left says account)
2. go to security -> signing in to google -> 2-step verification : turn it on and go through the process
3. go back to security -> signin to google then click on app passwords and generate a new one.
4. create a passcode.key file in this directory and add googles generated passcode with this format:
```
{
    "email": "your-email@gmail.com", 
    "source_email": "where-you-want-emails-sent-from@gmail.com", 
    "destination_email": "where-you-want-them-sent-to@gmail.com", 
    "password": "passcode-google-gave-you"
}
```