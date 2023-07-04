# python imports
import os
import subprocess

import json


# external libs imports
from fastapi import FastAPI, Form, Response, Request, HTTPException
from twilio.twiml.messaging_response import MessagingResponse
from twilio.request_validator import RequestValidator

# custom imports
from prettyPrint import printError, printInfo, printSuccess, welcome_message


# attach server instance to this with uvicorn server:app --reload
app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


# phone number to config map:
with open("./config/serverconfig.json") as json_file:
    phone_to_config = json.load(json_file)


def start(config_path: str):
    printInfo("Starting bot...")
    subprocess.Popen(
        ["python", "main.py", "--config", config_path])
    printSuccess("Bot started!")
    return "success"

def stop(config_path: str):
    """
    finds the pid of the bot and kills it. the output of ps looks like:
    PID TTY           TIME CMD
    698 ttys000    0:00.29 -zsh
    984 ttys002    0:00.34 /bin/zsh -il
    2066 ttys002    0:00.41 /opt/homebrew/Cellar/python@3.11/3.11.2_1/Frameworks/Python.framework/Versions/3.11/Resources/Python.app/Contents/MacOS/Python main.py -c ./configs/myconfig.json
    """
    printInfo("Stopping bot...")
    ps = subprocess.run(["ps"], capture_output=True, text=True)
    if ps.returncode != 0:
        printError("Error getting process list")
        return
    lines = ps.stdout.splitlines()
    for line in lines:
        if config_path in line:
            pid = line.split()[0]
            kill = subprocess.Popen(["kill", pid])
            if kill.returncode != 0:
                printError("Error stopping bot")
                break
            printSuccess("Bot stopped!")
            return "success"

    return "failed to stop bot."

def restart(config_path: str):
    stop(config_path)
    start(config_path)

def filter(config_path: str, filter: str):
    ...

def remove_filter(config_path: str, filter: str):
    ...

def help(config_path: str):
    ...

def add_link(config_path: str, link: str):
    ...

def remove_link(config_path: str, link: str):
    ...



# TODO:
# 1. Why does fastAPI require capitol letters for the first letter of the params?
@app.post("/text")
async def text(
    request: Request, From: str = Form(...), Body: str = Form(...)
):
    validator = RequestValidator(os.environ["TWILIO_AUTH_TOKEN"])
    form = await request.form()
    if not validator.validate(
        str(request.url),
        form,
        request.headers.get("X-Twilio-Signature", "")
    ):
        raise HTTPException(
            status_code=400, detail="Error in Twilio Signature")

    response = MessagingResponse()


    # begin management:
    printInfo(f"Received text from {From}: {Body}")

    config_path = phone_to_config.get(From, "./config/config.json")
    cmd = [c.lower() for c in Body.split()]

    if cmd[0] != "bot":
        response.msg(
            'Please start your message with "bot", available commands are "bot start" and "bot stop"')
        return Response(content=str(response), media_type="application/xml")


    # I wanted to make this a dict of functions but I couldn't figure out how to pass different arguments to each function
    # maybe the **kwargs thing?
    match cmd[1]:
        case "start":
            resp = start(config_path)
            response.message(resp)
        case "stop":
            resp = stop(config_path)
            response.message(resp)
        case "restart":
            resp = restart(config_path)
            response.message(resp)
        case "filter":
            resp = filter(config_path, cmd[2:].join(" "))
            response.message(resp)
        case _:
            response.msg(
                'Please start your message with "bot", available commands are "bot start" and "bot stop"')

    return Response(content=str(response), media_type="application/xml")
