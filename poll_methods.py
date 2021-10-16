import os
import re
import ast
import PyDictionary
from wonderwords import RandomWord
import random
from slack import WebClient
from dotenv import load_dotenv
import poll


# loads .env file / environment vars for secret params
load_dotenv()

slack_client = WebClient(os.environ["slack_key"])
slack_user_client = WebClient(os.environ["slack_user_key"])
slack_user_name = "PollSetter"
test_channel = os.environ["test_channel"]

# Misc Set Up
dictionary = PyDictionary.PyDictionary()
version_number = os.environ["version_number"]
poll_posts = dict()


# Post an image to a channel (using image url)
def send_photo_post(send_to_channel_id, message, image_url, reaction, title, user):
    response = slack_client.chat_postMessage(
        channel=send_to_channel_id,
        text=message,
        as_user=True,
        link_names=True,
        attachments=[{"title": title, "image_url": image_url}],
        username=user,
        unfurl_links=False
    )

    timestamp = response["ts"]
    if reaction != "":
        post_reaction(send_to_channel_id, reaction, timestamp)

    return timestamp


# Posts reactions as Alignment Bot
def post_reaction(react_channel_id, reaction_name, timestamp):
    slack_client.reactions_add(
        channel=react_channel_id,
        name=reaction_name,
        timestamp=timestamp
    )


# Responds in a thread
def send_thread_message(send_to_channel_id, original_msg_ts, message):
    response = slack_client.chat_postMessage(
        channel=send_to_channel_id,
        thread_ts=original_msg_ts,
        text=message,
        as_user=True,
        link_names=True,
        username=slack_user_name
    )

    return response["ts"]


# Sends message to a channel
def send_channel_message(send_to_channel_id, message, reaction):
    response = slack_client.chat_postMessage(
        channel=send_to_channel_id,
        text=message,
        as_user=True,
        link_names=True,
        username=slack_user_name
    )

    timestamp = response["ts"]
    if reaction != "":
        post_reaction(send_to_channel_id, reaction, timestamp)

    return timestamp


# Sends message as fake user
def send_faux_message(send_to_channel_id, message, parent_post_ts, user_name, reaction_image):
    response = slack_client.chat_postMessage(
        channel=send_to_channel_id,
        thread_ts=parent_post_ts,
        text=message,
        link_names=True,
        username=user_name,
        icon_emoji=reaction_image
    )

    return response["ts"]


# Delete a message
def delete_message(delete_from_channel_id, timestamp):
    response = slack_user_client.chat_delete(
        channel=delete_from_channel_id,
        ts=timestamp,
        as_user="true"
    )

    return response


# For sentences that depend on booleans.
def bool_translation(tf, true_phrase, false_phrase):
    if tf:
        return true_phrase
    return false_phrase


# Status update, confirm version_number. TNG s5e11 :)
def bot_check_in():
    return "I have received your message. I seem to be operating within expected parameters. I am currently " \
           "running PollSetter " + version_number + "."
    # add status for any other listeners/streams


# Add a new poll
def add_poll(event_data):
    # Parse data
    poll_command_str = re.sub("[^0-9a-zA-Z-.]+", " ", event_data["text"]).split()

    is_anon = 'ANON' in poll_command_str[0]  # will be [POLL] or [ANON-POLL]
    channel = poll_command_str[1]
    duration = poll_command_str[3]
    multi_vote = poll_command_str[4].lower() in ['true', 't', '1', 'y', 'yes']  # will be True or False
    valid_votes = ast.literal_eval(str(re.findall(r'{.*?}', event_data["text"])[0]))
    message = str(re.findall(r'"([^"]*)"', event_data["text"])[-1])

    new_poll = poll.Poll(is_anon, channel, duration, multi_vote, message, valid_votes,
                         event_data["user"], event_data["event_ts"])

    return new_poll


def generate_faux_name():
    r = RandomWord()
    new_name = \
        r.word(include_parts_of_speech=["adjectives"]).capitalize() + " " +\
        r.word(include_parts_of_speech=["nouns"]).capitalize()

    return new_name


def generate_faux_photo_id():
    return random.choice(list(slack_client.emoji_list()["emoji"].keys()))
