
# read this abt being undetected.
https://stackoverflow.com/questions/70709168/detected-on-headless-chrome-selenium

installed firefox with 
`sudo apt install firefox-esr` # this gave me Mozilla Firefox 102.9esr

download the gecko driver, i am running 64bit raspbian so need geckodriver 32

url="https://github.com/mozilla/geckodriver/releases/download/v0.32.2/geckodriver-v0.32.2-linux-aarch64.tar.gz"

curl -s -L "$url" | tar -xz
chmod +x geckodriver
sudo mv geckodriver /usr/local/bin/


**documentation from twilio on this part**:
https://www.twilio.com/blog/build-secure-twilio-webhook-python-fastapi

**to get fastapi working**:
```
pip install fastapi
```
```
pip install "uvicorn[standard]"
```

**to run the server**:
```
uvicorn server:app --reload
```


check if it's running by going to: http://127.0.0.1:8000/test

check the docs: http://127.0.0.1:8000/docs

Now use ngrok to make the port available (you'll prob need to set up ngrok, i have a free acount)
```
ngrok http 8000
```

Now take the url that ngrok gives and go to the twilio console -> phone numbers -> manage -> active numbers -> the phone number -> message configuration and then paste in the ngrok link where it says "a message comes in (webhook) URL"

