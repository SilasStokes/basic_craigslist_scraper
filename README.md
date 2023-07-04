# basic_craigslist_scraper

Goal of this repo is to flesh out what it takes to scrape craigslist before I port the [craigslist python package](https://github.com/juliomalegria/python-craigslist) to use selenium instead of requests due to craigslist blocking requests that don't come from a browser with javascript enabled, [documented here](https://github.com/juliomalegria/python-craigslist/issues/116)

To install the python packages use `pip install -r requirements.txt`.

# Todo List:
- [ ] Add a feature where all the texts will get added to a single text. 
- [ ] add the math to calculate the scraped time and the posted at (which cl presents as "4 mins ago") so timing can be correctly stored in the db. 
- [ ] create a parent scripts that can schedule and manage all the individual profiles in ./configs. (make an active directory in configs and put all the configs that need to be managed there)
- [ ] Allow the script to be managed via the user texting the twilio number e.g user can start and stop, add a new link, give filter keywords.
- [ ] Add filter section to config, no more notifications about free dirt. 
- [ ] Use Python package Fake User Agent to randomly generate a new user agent every request. 
- [ ] Use logging instead of prints
- [ ] correct the database datatypes, right now they are all strings...
- [ ] make the scraped_at property a foreign key
- [ ] dockerize the script so it's easily deployable for others


# Done
- [x] parse config file using something like dataclass or pydantic so inputs are autovalidated
- [x] Use SQLAlchemy 2.0 feature where you can you db model as dataclass. [like this](https://docs.sqlalchemy.org/en/20/orm/dataclasses.html)
- [x] clean up the database interpolation. 
- [x] write the code to integrate with twilio to get notifications via sms. 
- [x] allow human readable csv files to be selected instead of database (maybe command line argument?)
- [x] change the scrape function to account for multiple urls in the craigslist url array in the config.json
- [x] save the time that the post was posted + include that in the text. 

# Setup:

## Requirements

* A 64 bit raspberry pi running a 64 bit OS (ubuntu or similar)
* Python 3.9 - standalone or via [pyenv](https://github.com/pyenv/pyenv)
* firefox - `apt install firefox` *geckodriver included!*
* postgresql

once installed run `pip install -r requirements.txt`

### Postgrest setup

**NOTE:** If you already have postgres setup skip to step 4

1. Install with `apt install postgresql`
2. login to postgres `sudo -u postgres psql`
3. set the password `\password postgres`
4. create the database `CREATE DATABASE craigslist;`

Finally, update your `config.json` with your username and password (both are set to `postgres` here)

### To run:
```sh
python main.py -c ./path/to/your/config
```
when the `-c` config path is not passed it's assumed to be `./config/config.json`

### control the scraper via text message:
first you'll need to set up a `serverConfig.json` in the `./config` directory. An example file stubbed there currently. The server config file is necessary because I am running the bot for several of my friends, through my single twilio number, and I wanted them to have a way to control the bot remotely. But to do that, I needed to associate their phone number with their unique config file. 

Install the additional dependencies:
```sh
pip install fastapi
pip install "uvicorn[standard]"
```

Set up `ngrok`. If you don't have an account/auth_token, you'll have to set one up. Instructions linked here: https://ngrok.com/download.


Run the `server.py` file, using 
```sh
uvicorn server:app --reload
```
open a new terminal. We're going to connect `ngrok` to our locally hosted fastapi instance, which is served by default on `http://127.0.0.1:8000/`.
```sh
ngrok http 8000
```
Now take the url that ngrok gives and go to the twilio console -> phone numbers -> manage -> active numbers -> the phone number -> message configuration and then paste in the ngrok link where it says "a message comes in (webhook) URL"

Available commands to text the bot are:
```
All commands are case insensitive. 

bstart - start the bot
bstop - stop the bot
re - restart the bot

h - print this help message

f <filter> - add a filter to the bot
rf <filter> - remove a filter from the bot
lf - list all filters
l <link> - add a link to the bot
ll - list all links
rl <index> - remove a link from the bot, use "ll" to see indexes
```


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
