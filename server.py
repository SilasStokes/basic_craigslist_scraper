# python imports
import os
import subprocess


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
        raise HTTPException(status_code=400, detail="Error in Twilio Signature")
    
    response = MessagingResponse()
    # begin management:
    printInfo(f"Received text from {From}: {Body}")
    cmd = [c.lower() for c in Body.split()]
    if cmd[0] != "bot":
        response.msg('Please start your message with "bot", available commands are "bot start" and "bot stop"')
        return Response(content=str(response), media_type="application/xml")

    match cmd[1]:
        case "start":
            printInfo("Starting bot...")
            subprocess.Popen(["python", "main.py", "--config", "./configs/myconfig.json"])
            response.message("Bot started!")
        case "stop":
            printInfo("Stopping bot...")
            subprocess.Popen(["pkill", "-f", "main.py"])
            response.message("Bot stopped")
        case _:
            response.msg('Please start your message with "bot", available commands are "bot start" and "bot stop"')

    return Response(content=str(response), media_type="application/xml")
