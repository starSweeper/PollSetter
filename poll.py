import pollSetter
import datetime
import users


class Poll:
    def __init__(self, is_anon, channel, duration, multi_vote, message, valid_votes, user, post_ts):
        self.is_anon = is_anon
        self.channel = channel
        self.duration = duration
        self.multi_vote = multi_vote
        self.message = message
        self.valid_votes = valid_votes
        self.user = user
        self.post_ts = post_ts
        self.poll_end_ts = float(self.post_ts) + (3600 * float(self.duration))
        self.poll_end_date = datetime.datetime.fromtimestamp(self.poll_end_ts).strftime('%A, %x at %I:%M:%S %p %Z')
        self.faux_users = dict()

    # Create and post message announcing poll and the rules for it
    def post_poll(self):
        poll_message = "Poll created by <@" + self.user + ">, you " + \
                       pollSetter.bool_translation(self.multi_vote, "may ", "may not ") + \
                       "vote for multiple options. This poll " +\
                       pollSetter.bool_translation(self.is_anon, "is ", "is not ") + "anonymous!\n\n>" + self.message + "\n\n"

        for vote in self.valid_votes:
            poll_message += "- To vote for " + vote + ", react with " + self.valid_votes.get(vote) + "\n"

        poll_message += "\nPoll closes " + self.poll_end_date + "."

        pollSetter.send_channel_message(self.channel, poll_message, '')

    def handle_thread_post(self, event_data):
        # save message
        message_contents = event_data["text"]
        # delete post
        pollSetter.delete_message(self.channel, event_data["ts"])
        # repost message
        pollSetter.send_channel_message(self.channel, message_contents, '')

    def end_poll(self, message):
        # post message (poll results or cancellation message)
        pollSetter.send_channel_message(self.channel, message, '')
        # remove poll from txt file

    # Create message for posting poll results
    def create_results(self):
        results = self.message  # this is nonsense. This should be, I don't know. Not this...
        return results

    def add_new_user(self, user_id):
        faux_name = "Blue Coyote"
        faux_photo = "coyote.png"
        self.faux_users[user_id] = users.Users(user_id, self.post_ts, faux_name, faux_photo)

    def get_faux_users(self):
        return self.faux_users
