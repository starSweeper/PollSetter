class Users:
    faux_name = ''
    faux_photo_id = ''

    def __init__(self, user_id, post_ts, faux_name, faux_photo_id):
        self.user_id = user_id
        self.post_ts = post_ts
        self.cast_votes = []
        self.has_voted = False
        Users.faux_name = faux_name
        Users.faux_photo_id = faux_photo_id
