import json
import os
from slack_sdk import WebClient
import json
import slack
import os
from pathlib import Path
from flask import Flask, make_response
from flask import request
from pathlib import Path
from dotenv import load_dotenv
from slackeventsapi import SlackEventAdapter

env_path = Path(".")/ '.env'
load_dotenv(dotenv_path=env_path)
app = Flask(__name__)
slack_event_adapter = SlackEventAdapter(os.environ['SIGNING_SECRET'],'/slack/events',app)

client = slack.WebClient(token=os.environ['SLACK_TOKEN'])
#client.chat_postMessage(channel='#test',text='test1')
BOT_ID = client.api_call("auth.test")['user_id']
events = ["none"]
respondedevents = []

firstMessage = """:alert-triangle: For Critical Issues or Urgent Assistance, call AV Techsupport `+44 123787 9271`\nPlease provide the following details for quicker debugging System where you experience issue\n• (`AVCMP`, `Tunneler`, `Encoder`, `etc`)\n• `AVCMP Content ID` or `Sportradar Match ID`\n• Product with issue (`LCO`, `LCR`, `LCT`, `SpOTT`, etc)\nYou can respond with the event-/and content-id for links to the AVCMP and VMP"""
def addevent(event):
    events.append(event)

def addresponse(ts):
    respondedevents.append(ts)

def getResponses(ts):
    count = 0
    for x in range(0,len(respondedevents)):
        if respondedevents[x] == ts:
            count += 1
    return count

BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
# Create a Slack client using the bot token
client = WebClient(token=BOT_TOKEN)

def lambda_handler(payload, context):
    # Parse the incoming event data from Slack
    slack_event = json.loads(payload["body"])

    # Check for URL verification during the event subscription process
    if slack_event.get("type") == "url_verification":
        # Respond with the challenge token to verify the endpoint
        return {"statusCode": 200, "body": slack_event.get("challenge")}
    elif payload.get('type') == 'event_callback':
            event = payload.get('event', {})
            channel_id = event.get('channel')
            user_id = event.get('user')
            text = event.get('text')
            ts = event.get('ts')
            thread_ts = event.get('thread_ts')
            if str(thread_ts) == 'None': thread_ts = event.get('ts')
            #lastthread = response.get_lastthread()
            if events[len(events)-1] != "none": 
                lastthread = events[len(events)-1].get('text')
            else:
                lastthread = "None"

            if user_id != BOT_ID:
                
                addresponse(thread_ts)
                threadresponses = getResponses(thread_ts)
                if threadresponses == 1:
                    printmessage(threadresponses,event)
                elif threadresponses == 2:
                    printmessage(threadresponses,event)
                elif threadresponses > 2 and text.lower() == "this issue has been resolved":
                    client.reactions_add(channel=channel_id, timestamp = ts, name="stonks")
            return 'HTTP 200 OK'
    else:
        # Default response for other types of events or unhandled scenarios
        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": "hello world",
                }
            ),
        }
    
def printmessage(number, event):
    channel_id = event.get('channel')
    ts = event.get('ts')
    text = event.get('text')
    eventid = ' '
    sendmessage = True
    message = 'noevent'
    text = text.replace("=", ":")
    if str(text).lower().__contains__("event"):
        try:
            eventid = text.lower().split("event")[1].split(":")[1].replace(" ", "")[0:7]
        except IndexError:
            eventid = ""
        try:
            contentid = text.lower().split("content")[1].split(":")[1].replace(" ", "")[0:7]
        except IndexError:
            contentid = ""
        message = getMessage(eventid,contentid)
        #client.chat_postMessage(channel=channel_id, thread_ts = ts, text=str(message))

    if number > 1 and message == "noevent":
        sendmessage = False
    elif message == 'noevent':
        message = firstMessage

    if sendmessage: client.chat_postMessage(channel=channel_id, thread_ts = ts, text=str(message))

    
def getMessage(event,content):
    if event == "":
        return "noevent"
    else:
        if content =="":
            text = "Thank you here is the <http://avcmp.sportradar.com/events/" + str(event) + "|AVCMP Link>"
        else:
            text = "Thank you here is the <http://avcmp.sportradar.com/events/" + str(event) + "|AVCMP Link>\nand here is the <http://vpc.sportradar.ag/event-contents/" + str(content) + "|VMP Link>"
    return text
