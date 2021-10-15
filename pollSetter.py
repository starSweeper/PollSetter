import os
import io
import re
import ast
import PyDictionary
from slack import WebClient
from slack import RTMClient
from dotenv import load_dotenv
import poll

# loads .env file / environment vars for secret params
load_dotenv()

# Slack API Set Up
rtm_client = RTMClient(token=os.environ["rtm_client_token"])
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


# Posts reactions as Alignment Bot Ears, I should combine this and post_reaction
def ears_post_reaction(react_channel_id, reaction_name, timestamp, ears_client):
    ears_client.reactions_add(
        channel=react_channel_id,
        name=reaction_name,
        timestamp=timestamp
    )


# Posts reactions as Alignment Bot
def post_reaction(react_channel_id, reaction_name, timestamp):
    slack_client.reactions_add(
        channel=react_channel_id,
        name=reaction_name,
        timestamp=timestamp
    )


# Responds in a thread as Alignment Bot Ears. I should combine this and send_thread_message
def ears_send_thread_message(send_to_channel_id, original_msg_ts, message, ears_client):
    response = ears_client.chat_postMessage(
        channel=send_to_channel_id,
        thread_ts=original_msg_ts,
        text=message,
        as_user=True,
        link_names=True,
        username=slack_user_name
    )

    return response["ts"]


# Responds in a thread as Alignment Bot.
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


# Sends message to a channel as Alignment Bot. Should be modified so that it can be used by Alignment Bot Ears as well
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


# Sends message to a channel as Alignment Bot. Should be modified so that it can be used by Alignment Bot Ears as well
def send_faux_message(send_to_channel_id, message, user_name, reaction_image):
    response = slack_client.chat_postMessage(
        channel=send_to_channel_id,
        text=message,
        as_user=False,
        link_names=True,
        username=user_name,
        icon_emoji=reaction_image
    )

    timestamp = response["ts"]

    return timestamp


# Delete a message
def delete_message(delete_from_channel_id, timestamp):
    response = slack_user_client.chat_delete(
        channel=delete_from_channel_id,
        ts=timestamp,
        as_user="true"
    )

    return response


# Called whenever a message is received in a channel PollSetter Ears has access to
@RTMClient.run_on(event="message")
def list_message(**payload):
    event_data = payload["data"]
    web_client = payload['web_client']

    is_thread_msg = True if "thread_ts" in event_data else False
    print(event_data)

    if "text" in event_data:
        event_text = event_data["text"]
        if event_text.startswith("[POLL"):
            add_poll(event_data)
        elif event_text.lower() in ("do you hear me?", "can you read me"):
            print("check in")
            send_channel_message(event_data["channel"], bot_check_in(), '')

        if is_thread_msg and (event_data["channel"] + event_data["ts"]) in poll_posts:
            print("poll thread detected")
            poll_key = (event_data["channel"] + event_data["thread_ts"])
            found_poll = poll_posts.get(poll_key)

            if event_data["user"] not in found_poll.get_faux_users():
                found_poll.add_new_user(event_data["user"])

            found_poll.handle_thread_post(event_data)
        else:
            print(poll_posts)
            print(event_data["channel"] + event_data["ts"])


# For sentences that depend on booleans.
def bool_translation(tf, true_phrase, false_phrase):
    if tf:
        return true_phrase
    return false_phrase


# Status update, confirm version_number
def bot_check_in():
    return "I have received your message. I seem to be operating within expected parameters. I am currently " \
            "running PollSetter " + version_number + "."


# Add a new poll
def add_poll(event_data):
    # Parse data
    poll_command_str = re.sub("[^0-9a-zA-Z-.]+", " ", event_data["text"]).split()

    is_anon = 'ANON' in poll_command_str[0]  # will be [POLL] or [ANON-POLL]
    channel = poll_command_str[1]
    duration = poll_command_str[3]
    multi_vote = poll_command_str[4].lower() in ['true', '1', 'y', 't']  # will be True or False
    valid_votes = ast.literal_eval(str(re.findall(r'{.*?}', event_data["text"])[0]))
    message = str(re.findall(r'"([^"]*)"', event_data["text"])[-1])

    new_poll = poll.Poll(is_anon, channel, duration, multi_vote, message, valid_votes,
                         event_data["user"], event_data["ts"])

    new_poll.post_poll()  # Post poll message
    poll_posts[event_data["channel"] + event_data["ts"]] = new_poll


def main():
    slack_client.conversations_join(channel=test_channel)
    send_channel_message(test_channel, "Set up complete! Running pollSetter v." + version_number, "tada")

    # Listen for slack messages
    rtm_client.start()


if __name__ == '__main__':
    main()
