# basic_craigslist_scraper

Goal of this repo is to flesh out what it takes to scrape craigslist before I port the [craigslist python package](https://github.com/juliomalegria/python-craigslist) to use selenium instead of requests due to craigslist blocking requests that don't come from a browser with javascript enabled, [documented here](https://github.com/juliomalegria/python-craigslist/issues/116)

To install the python packages use `pip install -r requirements.txt`.

goals:
1. write a script that can pull from craigslist 24/7 without bot detection. 
2. send me alerts via email or text when a new ad I want to see becomes available.
3. create the program such that it's usable by others with little to no code set up. 
4. have the script alert me if it stops running
