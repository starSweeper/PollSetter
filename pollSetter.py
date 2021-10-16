import os
import PyDictionary
from slack import WebClient
from slack import RTMClient
from dotenv import load_dotenv
import poll_methods


# loads .env file / environment vars for secret params
load_dotenv()

# Slack API Set Up
rtm_client = RTMClient(token=os.environ["rtm_client_token"])
slack_client = WebClient(os.environ["slack_key"])


test_channel = os.environ["test_channel"]

# Misc Set Up
dictionary = PyDictionary.PyDictionary()
version_number = os.environ["version_number"]
poll_posts = dict()


@RTMClient.run_on(event="reaction_added")
def get_reactions(**payload):
    event_data = payload["data"]
    reaction = event_data["reaction"]
    channel = event_data["item"]["channel"]
    timestamp = event_data["item"]["ts"]

    if (channel + timestamp) in poll_posts:
        poll_key = (channel + timestamp)
        found_poll = poll_posts.get(poll_key)

        poll_methods.remove_reaction(reaction, channel, timestamp)

        # Create a new user fpr the poll if not exists
        if event_data["user"] not in found_poll.get_faux_users():
            found_poll.add_new_user(event_data["user"])

        # Count the vote
        found_poll.add_vote(reaction, event_data["user"])


# Called whenever a message is received in a channel PollSetter Ears has access to
@RTMClient.run_on(event="message")
def list_message(**payload):
    event_data = payload["data"]

    is_thread_msg = True if "thread_ts" in event_data else False
    is_bot_post = True if "bot_id" in event_data else False

    if "text" in event_data and not is_bot_post:
        event_text = event_data["text"]

        # Poll request
        if event_text.startswith("[POLL"):
            new_poll = poll_methods.add_poll(event_data)  # Create a new poll, post it, and save it to poll_posts
            poll_posts[event_data["channel"] + new_poll.post_poll()] = new_poll  # Post poll message and save Poll
        # Bot status
        elif event_text.lower() in ("do you hear me?", "can you read me"):
            poll_methods.send_channel_message(event_data["channel"], poll_methods.bot_check_in(), '')

        if is_thread_msg and (event_data["channel"] + event_data["thread_ts"]) in poll_posts:
            poll_key = (event_data["channel"] + event_data["thread_ts"])
            found_poll = poll_posts.get(poll_key)

            # Create a new user fpr the poll if not exists
            if event_data["user"] not in found_poll.get_faux_users():
                found_poll.add_new_user(event_data["user"])

            # Save, delete, and repost message
            found_poll.handle_thread_post(event_data)


if __name__ == '__main__':
    slack_client.conversations_join(channel=test_channel)
    poll_methods.send_channel_message(test_channel, "Set up complete! Running pollSetter v." + version_number, "tada")

    # Listen for slack messages
    rtm_client.start()
