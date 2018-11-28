#!/usr/bin/env python2

from __future__ import print_function
import datetime
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
import logging
import os
import sys
import argparse
import random

# If modifying these scopes, delete the file token.json.
SCOPES = 'https://www.googleapis.com/auth/calendar.events'

parser = argparse.ArgumentParser(description='automatically reply to events in gcal')
parser.add_argument('-t', '--token', help='path of token.json', type=str, default='token.json')
parser.add_argument('-c', '--creators', help='path of creators.txt', type=str, default='creators.txt')
parser.add_argument('--noauth_local_webserver', action="store_true", default=1)
parser.add_argument('-d', '--cred', help='path of credentials.json', type=str, default='credentials.json')
parser.add_argument('-r', '--response', help='sets the response type that will be sent', type=str, default='accepted', choices=['accepted', 'declined', 'tentative'])
parser.add_argument('--random', help='sets the response to a random choice perfect for irratating management', default=False, action='store_true')
parser.add_argument('-v', '--verbose', help='logs to console', default=False, action='store_true')
parser.add_argument('--whatif', help='logs but does not update event', default=False, action='store_true')
args = parser.parse_args()

# creators.txt in the same directory contains a list of emails, one per line,
# these are the creators that will be automatically replied to
with open(args.creators, 'r') as f:
    CREATORS = []
    for creator in f:
        CREATORS.append(creator.strip())


# since this is meant to run in cron, keep logs
# create /var/og/maybe.log manually and chown
# to whatever user is running the script
logger = logging.getLogger('auto-maybe')
logger.setLevel(logging.INFO)
fh = logging.FileHandler('/var/log/maybe.log')
fh.setLevel(logging.INFO)
ff = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(ff)
ch = logging.StreamHandler()
if args.verbose or args.whatif:
    ch.setLevel(logging.INFO)
else:
    ch.setLevel(logging.WARNING)
logger.addHandler(fh)
logger.addHandler(ch)

logger.info("creators: " + str(CREATORS))


def main():


    """Shows basic usage of the Google Calendar API.
    most of this comes from Google's quickstart guide
    """
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    store = file.Storage(args.token)
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets(args.cred, SCOPES)
        creds = tools.run_flow(flow, store)
        logger.error("credentials invalid")
    service = build('calendar', 'v3', http=creds.authorize(Http()))

    # Call the Calendar API
    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    logger.info('Getting the upcoming 10 events')
    events_result = service.events().list(calendarId='primary', timeMin=now,
                                        maxResults=10, singleEvents=True,
                                        orderBy='startTime').execute()
    events = events_result.get('items', [])
    updated_something = False;
    if not events:
        logger.warning('No upcoming events found.')
    for event in events:
        if event.has_key('creator') and event.has_key('attendees'):
            if event['creator'].get('email') in CREATORS:
                for attendee in event['attendees']:
                    if attendee.get('self'):
                        status = attendee.get('responseStatus')
                        if status == 'needsAction':
                            if not args.random:
                                response = args.response
                            else:
                                rlist = ['accepted', 'tentative', 'declined']
                                response = random.choice(rlist)
                                logger.info("random response selected " + str(response))
                            start = event['start'].get('dateTime', event['start'].get('date'))
                            attendee['responseStatus'] = response
                            updated_something = True;
                            if not args.whatif:
                                service.events().update(calendarId='primary',
                                                   eventId=event['id'],
                                                   sendUpdates='none',
                                                   body=event).execute()
                                logger.info('replied ' + response + ' to: ' + start + " " + event['summary'])
                            else:
                                logger.warning('would reply ' + response +
                                               ' to: ' + start + ' ' +
                                               event['summary'])
    if not updated_something:
        logger.info('No relevant events found')
if __name__ == '__main__':
    main()
