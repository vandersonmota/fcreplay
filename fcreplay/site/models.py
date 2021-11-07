from fcreplay.site.database import db


class Replays(db.Model):
    id = db.Column(db.Text, primary_key=True)
    p1_loc = db.Column(db.String)
    p2_loc = db.Column(db.String)
    p1_rank = db.Column(db.String)
    p2_rank = db.Column(db.String)
    p1 = db.Column(db.String)
    p2 = db.Column(db.String)
    date_replay = db.Column(db.DateTime)
    length = db.Column(db.Integer)
    created = db.Column(db.Boolean)
    failed = db.Column(db.Boolean)
    status = db.Column(db.String)
    date_added = db.Column(db.DateTime)
    player_requested = db.Column(db.Boolean)
    game = db.Column(db.String)
    video_processed = db.Column(db.Boolean)
    video_youtube_uploaded = db.Column(db.Boolean)
    video_youtube_id = db.Column(db.String)
    fail_count = db.Column(db.Integer)
    ia_filename = db.Column(db.String)


class Descriptions(db.Model):
    id = db.Column(db.Text, primary_key=True)
    description = db.Column(db.Text)


class Character_detect(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    challenge_id = db.Column(db.Text, primary_key=True)
    p1_char = db.Column(db.String)
    p2_char = db.Column(db.String)
    vid_time = db.Column(db.String)
    game = db.Column(db.String)
