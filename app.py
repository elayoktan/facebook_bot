# pylint: disable-msg=C0111
# pylint: disable-msg=C0103
# pylint: disable-msg=W0603
# pylint: disable-msg=W0612
# pylint: disable-msg=C0301

import os
import sys
import json
import urllib
import requests
from flask import Flask, request



app = Flask(__name__)
origin = {'init_key':'init_val'}
destination = {'init_key':'init_val'}
date = {'init_key':'init_val'}

VERIFY_TOKEN = "WEUu0NnceuU1l13eSffw"

@app.route('/', methods=['GET'])
def verify():
    """ when the endpoint is registered as a webhook, it must echo back
    the 'hub.challenge' value it receives in the query arguments""" '''os.environ["VERIFY_TOKEN"]:'''
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200

    return "Hello world", 200


@app.route('/', methods=['POST'])
def webhook():
    """To link the webhook with our webserver. This checks if there is a new message or not"""
    data = request.get_json()
    log(data)
    global origin
    global destination
    global date
    if data["object"] == "page":
        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:
                if messaging_event.get("message"):  # trigger when a message is sent to us
                    sender_id = messaging_event["sender"]["id"]        # the message sender's Facebook ID
                    recipient_id = messaging_event["recipient"]["id"]  # Facebook ID of our page
                    message_text = messaging_event["message"]["text"]  # the message itself
                    paramsList = message_text.split(",")
                    try:
                        origin[sender_id] = paramsList[0]
                        destination[sender_id] = paramsList[1]
                        date[sender_id] = paramsList[2]
                    except ValueError:
                        log("Index error")
                    try:
                        url = "http://partners.api.skyscanner.net/apiservices/browsequotes/v1.0/TR/try/en-GB/"+origin[sender_id]+"/"+destination[sender_id]+"/"+date[sender_id]+"/?apikey=prtl6749387986743898559646983194"
                        response = urllib.request.urlopen(url)
                        data = json.loads(response.read())
                        log(data)
                        planenames = ""
                        for quote in data["Quotes"]:
                            try:
                                for cid in quote["OutboundLeg"]["CarrierIds"]:
                                    try:
                                        for plane in data["Carriers"]:
                                            if plane["CarrierId"] == cid:
                                                planenames = str(plane["Name"])
                                    except ValueError:
                                        log("plane")
                            except ValueError:
                                log("cid")
                            datetime = str(quote["OutboundLeg"]["DepartureDate"]).split('T')
                            if datetime[1] == "00:00:00":
                                send_message(sender_id, str(planenames) + " \nDate: " + datetime[0] + " \nPrice: " +str(quote["MinPrice"])+"TL")
                            else:
                                send_message(sender_id, str(planenames) + " \nDate: " + datetime[0] + " \nTime: " + datetime[1] + " \nPrice: " +str(quote["MinPrice"])+"TL")
                    except ValueError:
                        log("Session error")
                if messaging_event.get("delivery"):
                    pass

                if messaging_event.get("optin"):
                    pass

                if messaging_event.get("postback"):
                    pass

    return "ok", 200



def send_message(recipient_id, message_text):
    """To send the message_text to someone with recipient_id"""
    log("sending message to {recipient}: {text}".format(recipient=recipient_id, text=message_text))

    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": message_text
        }
    })
    req = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if req.status_code != 200:
        log(req.status_code)
        log(req.text)


def log(message):
    """To put the errors and valuable data into logs"""
    print(message)
    sys.stdout.flush()


if __name__ == '__main__':
    app.run(debug=True)
