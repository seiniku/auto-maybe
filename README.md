# auto-maybe
Auto-maybe is a script which automatically replies to calandar events in google cal. I've been assured by management that replying to meeting invitations is professional and will result in larger raises. Since I disagree and find it a waste of time (google adds the events to the calendar automatically), I've wasted time to automate the replies to selected addresses. 

Who knows, maybe it will pay off some day. /s

Requires google api python client and oath2client
```
pip install --upgrade google-api-python-client oauth2client
```

It currently logs to /var/log/maybe.log, which needs to be manually created
```
sudo touch /var/log/maybe.log
sudo chown user:group /var/log/maybe.log
```

Run once interactively to create credential files:
```
python auto-maybe.py --noauth_local_webserver
```
If running in cron, use something like this:
```
2 11 * * 1-5 /home/username/git/auto-maybe/auto-maybe.py -t /home/username/git/auto-maybe/token.json
```
