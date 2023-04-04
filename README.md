# basic_craigslist_scraper

Goal of this repo is to flesh out what it takes to scrape craigslist before I port the [craigslist python package](https://github.com/juliomalegria/python-craigslist) to use selenium instead of requests due to craigslist blocking requests that don't come from a browser with javascript enabled, [documented here](https://github.com/juliomalegria/python-craigslist/issues/116)

To install the python packages use `pip install -r requirements.txt`.

# Todo List:
- [ ] Use Python package Fake User Agent to randomly generate a new user agent every request. 
- [ ] Use logging instead of prints
- [ ] correct the database datatypes, right now they are all strings...
- [ ] make the scraped_at property a foreign key
- [ ] dockerize the script so it's easily deployable for others
- [ ] create a parent scripts that can schedule and manage all the individual profiles in ./configs. 


# Done
- [x] parse config file using something like dataclass or pydantic so inputs are autovalidated
- [x] Use SQLAlchemy 2.0 feature where you can you db model as dataclass. [like this](https://docs.sqlalchemy.org/en/20/orm/dataclasses.html)
- [x] clean up the database interpolation. 
- [x] write the code to integrate with twilio to get notifications via sms. 
- [x] allow human readable csv files to be selected instead of database (maybe command line argument?)
- [x] change the scrape function to account for multiple urls in the craigslist url array in the config.json
- [x] save the time that the post was posted + include that in the text. 

# goals:
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

# to set up phone number: 
'''
TODO!
'''