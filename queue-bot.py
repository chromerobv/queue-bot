#!/usr/bin/env python
import os
import time
import pickle
from collections import deque
from slackclient import SlackClient
import os.path

# import out config
import config

# constants
AT_BOT = "<@" + config.BOT_ID + ">"
usernames = {}
the_file = "list.txt"
pong_queue = deque()
if os.path.isfile(the_file) and os.stat(the_file).st_size != 0:
    with open(the_file, 'rb') as f:
        pong_queue = pickle.load(f)

# instantiate Slack & Twilio clients
slack_client = SlackClient(config.SLACK_KEY)

def handle_command(command, channel, username):
    """
        Receives commands directed at the bot and determines if they
        are valid commands. If so, then acts on the commands. If not,
        returns back what it needs for clarification.
    """
    global pong_queue
    global the_file
    response = "I understand:\n 'next': Place yourself in the queue.\n 'here': Remove yourself from queue if you are next.\n 'list': List all people in line."
    if command.startswith('next'):
        if username not in pong_queue:
            pong_queue.appendleft(username)
            response = "OK @" + username + " you are now in the queue!"
        else:
            response = "@" + username + " you are already in line!"    
    if command.startswith('here'):
        if len(pong_queue)>0:
            l = len(pong_queue)-1
            myList = pong_queue[l]
            if myList == username:
                user_off = pong_queue.pop()
                l = len(pong_queue)-1
                if len(pong_queue)>0:
                    upNext = "Up next is @" + pong_queue[l] + "!"
                else:
                    upNext = "No one is up next. Call next now!"
                response = "OK " + user_off + " has been removed from the queue!\n" + upNext
            else:
                response = "Sorry, only @" + myList + " can call here for themselves."
        else:
           response = "There is currently no one in the queue."
    if command.startswith('skip'):
        if len(pong_queue)>0:
            l = len(pong_queue)-1
            myList = pong_queue[l]
            if ADMIN_USER == username:
                user_off = pong_queue.pop()
                l = len(pong_queue)-1
                if len(pong_queue)>0:
                    upNext = "Up next is @" + pong_queue[l] + "!"
                else:
                    upNext = "No one is up next. Call next now!"
                response = "OK " + user_off + " has been removed from the queue!\n" + upNext
            else:
                response = "Sorry, only @" + ADMIN_USR + " can skip."
        else:
           response = "There is currently no one in the queue."
    if command.startswith('list'):
        if len(pong_queue)>0:
            myList = "\n\t-".join(reversed(pong_queue))
        else:
            myList = "list is emtpy."
        response = "Here is the current queue:\n\t-" + myList + "\n" 
    with open(the_file, 'wb') as f:
        pickle.dump(pong_queue, f)
    slack_client.api_call("chat.postMessage", channel=channel,
                          text=response, as_user=True)


def parse_slack_output(slack_rtm_output):
    """
        The Slack Real Time Messaging API is an events firehose.
        this parsing function returns None unless a message is
        directed at the Bot, based on its ID.
    """
    global usernames
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'text' in output and AT_BOT in output['text']:
                # return text after the @ mention, whitespace removed
                return output['text'].split(AT_BOT)[1].strip().lower(), \
                       output['channel'], usernames[output['user']]
    return None, None, None


if __name__ == "__main__":
    READ_WEBSOCKET_DELAY = 1 # 1 second delay between reading from firehose
    if slack_client.rtm_connect():
        print("StarterBot connected and running!")
        while True:
            api_call = slack_client.api_call("users.list")
            users = api_call.get("members")
            username_dicts = [{user["id"]: user["name"]} for user in users]
            for username in username_dicts:
                usernames.update(username)

            command, channel, user_name = parse_slack_output(slack_client.rtm_read())
            if command and channel:
                handle_command(command, channel, user_name)
            time.sleep(READ_WEBSOCKET_DELAY)
    else:
        print("Connection failed. Invalid Slack token or bot ID?")
