from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

# ----------------- User Model -----------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    playlists = db.relationship("Playlist", backref="user", lazy=True)
    favorites = db.relationship("Favorite", backref="user", lazy=True)
    recently_played = db.relationship("RecentlyPlayed", backref="user", lazy=True)
    queue = db.relationship("QueueItem", backref="user", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# ----------------- Artist Model -----------------
class Artist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    image_url = db.Column(db.String(500))
    songs = db.relationship('Song', backref='artist_obj', lazy=True)
    is_popular = db.Column(db.Boolean, default=False)  # Popular flag
# ----------------- Song Model -----------------
class Song(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'), nullable=True)
    album = db.Column(db.String(255))
    youtube_url = db.Column(db.String(500))
    image_url = db.Column(db.String(500))
    lyrics = db.Column(db.Text)
    is_public = db.Column(db.Boolean, default=True)

    tags = db.relationship('SongTag', backref='song', lazy=True)
    favorites = db.relationship('Favorite', backref='song', lazy=True)
    played_recently = db.relationship("RecentlyPlayed", backref="song", lazy=True)

# ----------------- Playlist Model -----------------
class Playlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    songs = db.relationship('Song', secondary='playlist_song', backref='playlists')

class PlaylistSong(db.Model):
    __tablename__ = 'playlist_song'
    playlist_id = db.Column(db.Integer, db.ForeignKey('playlist.id'), primary_key=True)
    song_id = db.Column(db.Integer, db.ForeignKey('song.id'), primary_key=True)

# ----------------- Song-Tag (Category) -----------------
class SongTag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    song_id = db.Column(db.Integer, db.ForeignKey('song.id'), nullable=False)
    tag = db.Column(db.String(50), nullable=False)

# ----------------- Favorite Songs -----------------
class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    song_id = db.Column(db.Integer, db.ForeignKey('song.id'), nullable=False)

# ----------------- Recently Played Songs -----------------
class RecentlyPlayed(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    song_id = db.Column(db.Integer, db.ForeignKey('song.id'))
    timestamp = db.Column(db.DateTime, server_default=db.func.now())

# ----------------- Playback Queue -----------------
class QueueItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    song_id = db.Column(db.Integer, db.ForeignKey('song.id'))
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    position = db.Column(db.Integer, nullable=True)  # Order in queue
    song = db.relationship('Song')
    # ----------------- Playback Settings -----------------
class PlaybackSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    shuffle = db.Column(db.Boolean, default=False)
    repeat_mode = db.Column(db.String(10), default='off')  # possible values: 'off', 'one', 'all'

    user = db.relationship('User', backref=db.backref('playback_settings', uselist=False))


    #............ADMIN....------------------

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), default="superadmin")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
# user favourite
class UserFavorites(db.Model):
    __tablename__ = 'user_favorites'

    id = db.Column(db.Integer, primary_key=True)  # Must have a primary key
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    song_id = db.Column(db.Integer, db.ForeignKey('song.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    # Optional: enforce unique combination of user and song
    __table_args__ = (db.UniqueConstraint('user_id', 'song_id', name='_user_song_uc'),)

