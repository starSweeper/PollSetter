import poll_methods
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
        self.parent_ts = ''
        self.vote_count = dict()

    # Create and post message announcing poll and the rules for it
    def post_poll(self):
        poll_message = "Poll created by <@" + self.user + ">, you " + \
                       poll_methods.bool_translation(self.multi_vote, "may ", "may not ") + \
                       "vote for multiple options. This poll " + \
                       poll_methods.bool_translation(self.is_anon, "is ", "is not ") + \
                       "anonymous!\n\n>" + self.message + "\n\n"

        for vote in self.valid_votes:
            reaction = self.valid_votes.get(vote)
            poll_message += "- To vote for " + vote + ", react with " + reaction + "\n"
            self.vote_count[reaction.replace(':', '')] = 0
            self.valid_votes[vote] = reaction.replace(':', '')

        self.vote_count["invalid"] = 0

        poll_message += "\nPoll closes " + self.poll_end_date + "."

        self.parent_ts = poll_methods.send_channel_message(self.channel, poll_message, '')

        return self.parent_ts

    def handle_thread_post(self, event_data):
        # save message
        message_contents = event_data["text"]

        # delete post
        poll_methods.delete_message(self.channel, event_data["ts"])

        # repost message
        poll_methods.send_faux_message(self.channel, message_contents, self.parent_ts,
                                       self.faux_users.get(self.user).faux_name,
                                       self.faux_users.get(self.user).faux_photo_id)

    def end_poll(self, message):
        # post message (poll results or cancellation message)
        poll_methods.send_channel_message(self.channel, message, '')
        # remove poll from txt file

    # Create message for posting poll results
    def create_results(self):
        results = self.message  # this is nonsense. This should be, I don't know. Not this...
        return results

    def add_new_user(self, user_id):
        faux_name = poll_methods.generate_faux_name()
        faux_photo = poll_methods.generate_faux_photo_id()
        self.faux_users[user_id] = users.Users(user_id, self.post_ts, faux_name, faux_photo)

    def get_faux_users(self):
        return self.faux_users

    def add_vote(self, reaction, user):
        faux_user = self.faux_users.get(user)
        if reaction in faux_user.cast_votes or (not self.multi_vote and faux_user.has_voted):
            self.vote_count["invalid"] += 1
            return False
        else:
            faux_user.cast_votes.append(reaction)
            faux_user.has_voted = True

            if reaction in self.valid_votes.values():
                self.vote_count[reaction] += 1
            else:
                self.vote_count["invalid"] += 1

        return True
