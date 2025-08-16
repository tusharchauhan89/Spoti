from flask import Flask, request, render_template, session, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from models import db, User, Song, Playlist, PlaylistSong, RecentlyPlayed, QueueItem, Favorite, Artist, PlaybackSettings
import requests

from flask_migrate import Migrate 
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///spotify_clone.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'supersecretkey'
app.debug = True
db.init_app(app)

migrate = Migrate(app, db)
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    playlists = Playlist.query.filter_by(user_id=session['user_id']).all()
    return render_template("player.html", playlists=playlists)

@app.route('/player')
def player():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    songs = Song.query.all()
    return render_template('player.html', songs=songs)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            return "Username already exists"
        if User.query.filter_by(email=email).first():
            return "Email already exists"

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            return redirect(url_for('index'))
        return "Invalid credentials"
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash("Logged out successfully!", "success")
    return redirect(url_for('login'))

@app.route('/profile')
def user_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    liked_count = len(user.favorites)
    recently_played_count = len(user.recently_played)
    playlist_count = len(user.playlists)

    return render_template('profile.html',
                           user=user,
                           liked_count=liked_count,
                           recently_played_count=recently_played_count,
                           playlist_count=playlist_count)

# -----------------------FOR SEARCHING SONGS
@app.route('/search')
def search():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    query = request.args.get('q', '').strip()
    if not query:
        return "No search query provided", 400

    url = f"https://saavn.dev/api/search/songs?query={query}"
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        data = res.json()

        results = data.get("data", {}).get("results", [])
        if not results:
            return render_template("search_results.html", query=query, songs=[])

        songs = []
        for song_data in results:
            # Title
            title = song_data.get("name") or "Unknown Title"

            # Artist Name
            primary_artists = song_data.get("primary_artists") or []
            if isinstance(primary_artists, str):
                artist_name = primary_artists
            elif isinstance(primary_artists, list):
                artist_name = ", ".join(primary_artists)
            else:
                artist_name = "Unknown Artist"

            # Artist object in DB
            artist_obj = Artist.query.filter_by(name=artist_name).first()
            if not artist_obj:
                artist_obj = Artist(name=artist_name)
                db.session.add(artist_obj)
                db.session.commit()

            # Image URL
            image_url = ""
            image_data = song_data.get("image")
            if isinstance(image_data, list) and image_data:
                image_url = image_data[-1].get("url", "")
            elif isinstance(image_data, str):
                image_url = image_data

            # Album
            album = song_data.get("album", {}).get("name") or "Unknown Album"

            # Audio URL (prefer 320kbps, then 128kbps)
            audio_url = ""
            download_url = song_data.get("downloadUrl")
            if isinstance(download_url, list):
                for item in reversed(download_url):
                    if isinstance(item, dict) and "url" in item:
                        audio_url = item["url"]
                        break
            elif isinstance(download_url, dict):
                audio_url = download_url.get("320") or download_url.get("128", "")

            # Lyrics
            lyrics = song_data.get("lyrics") or "Lyrics not available"

            # Save song in DB if not already there
            song_obj = Song.query.filter_by(name=title, artist_id=artist_obj.id).first()
            if not song_obj:
                song_obj = Song(
                    name=title,
                    artist_id=artist_obj.id,
                    album=album,
                    youtube_url=audio_url,
                    image_url=image_url,
                    lyrics=lyrics
                )
                db.session.add(song_obj)
                db.session.commit()

            # Append song to list for rendering
            songs.append({
                "id": song_obj.id,    
                "title": title,
                "artist": artist_name,
                "album": album,
                "url": audio_url,
                "image": image_url
            })

        return render_template("search_results.html", query=query, songs=songs)

    except requests.exceptions.RequestException as re:
        print(f"[ERROR] HTTP Request failed: {re}")
        return "Failed to fetch data from Saavn API", 500
    except Exception as e:
        print(f"[ERROR] General error in /search: {e}")
        return "An error occurred while searching", 500

# --------------CREATE PLAYLIST 


@app.route('/playlists/create', methods=['POST'])
def create_playlist():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    name = request.form.get('name')
    if not name:
        return "Playlist name required", 400

    playlist = Playlist(name=name, user_id=session['user_id'])
    db.session.add(playlist)
    db.session.commit()
    return redirect(url_for('list_playlists'))

@app.route('/playlists')
def list_playlists():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    playlists = Playlist.query.filter_by(user_id=session['user_id']).all()
    return render_template('playlists.html', playlists=playlists)

@app.route('/playlists/<int:playlist_id>/add', methods=['POST'])
def add_to_playlist(playlist_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    song_id = request.form.get('song_id')
    song_name = request.form.get('name')
    artist = request.form.get('artist')
    album = request.form.get('album')
    youtube_url = request.form.get('youtube_url') or ""
    image_url = request.form.get('image_url') or ""

    if not song_id or not song_name:
        return "Missing song ID or name", 400

    song = Song.query.get(song_id)
    if not song:
        song = Song(
            id=song_id,
            name=song_name,
            artist=artist,
            album=album,
            youtube_url=youtube_url,
            image_url=image_url
        )
        db.session.add(song)
        db.session.commit()

    existing = PlaylistSong.query.filter_by(playlist_id=playlist_id, song_id=song.id).first()
    if not existing:
        entry = PlaylistSong(playlist_id=playlist_id, song_id=song.id)
        db.session.add(entry)
        db.session.commit()

    return redirect(url_for('view_playlist', playlist_id=playlist_id))

@app.route('/playlists/<int:playlist_id>')
def view_playlist(playlist_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    playlist = Playlist.query.get_or_404(playlist_id)
    songs = playlist.songs
    return render_template('playlist_detail.html', playlist=playlist, songs=songs)
#...........playlist id.......

@app.route('/playlists/<int:playlist_id>/delete', methods=['POST'])
def delete_playlist(playlist_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    playlist = Playlist.query.filter_by(id=playlist_id, user_id=session['user_id']).first()
    if playlist:
        db.session.delete(playlist)
        db.session.commit()

    return redirect(url_for('list_playlists'))

@app.route('/playlists/<int:playlist_id>/songs/<int:song_id>/remove', methods=['POST'])
def remove_song_from_playlist(playlist_id, song_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    playlist_song = PlaylistSong.query.filter_by(playlist_id=playlist_id, song_id=song_id).first()
    if playlist_song:
        db.session.delete(playlist_song)
        db.session.commit()

    return redirect(url_for('view_playlist', playlist_id=playlist_id))

@app.route('/create_default_playlist')
def create_default_playlist():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    existing = Playlist.query.filter_by(user_id=session['user_id']).first()
    if not existing:
        playlist = Playlist(name="My Default Playlist", user_id=session['user_id'])
        db.session.add(playlist)
        db.session.commit()
        return "Default playlist created!"
    return "Playlist already exists!"

@app.route('/favorites/add', methods=['POST'])
def add_to_favorites():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    song_id = request.form.get('song_id')
    if not song_id:
        return "Song ID required", 400

    existing = Favorite.query.filter_by(user_id=session['user_id'], song_id=song_id).first()
    if not existing:
        fav = Favorite(user_id=session['user_id'], song_id=song_id)
        db.session.add(fav)
        db.session.commit()

    return redirect(url_for('index'))

@app.route('/favorites')
def view_favorites():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    fav_songs = Song.query.join(Favorite).filter(Favorite.user_id == session['user_id']).all()
    return render_template('favorites.html', songs=fav_songs)


# likee unlike btnn







@app.route('/recently-played')
def recently_played():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    entries = RecentlyPlayed.query.filter_by(user_id=user_id).order_by(RecentlyPlayed.timestamp.desc()).limit(25).all()
    songs = [entry.song for entry in entries]
    return render_template('recently_played.html', songs=songs)





#..........queue next 
@app.route('/queue/next', methods=['GET'])
def get_next_song():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'message': 'User not logged in'}), 403

    context = session.get('playback_context')

    # Fetch user queue
    queue_items = QueueItem.query.filter_by(user_id=user_id).order_by(QueueItem.added_at.asc()).all()
    queue_song_ids = [item.song_id for item in queue_items]

    # Initialize context if not exists
    if not context:
        if queue_song_ids:
            context = {'songs': queue_song_ids, 'current_index': 0}
        else:
            # fallback to all songs if queue is empty
            all_songs = Song.query.order_by(Song.id.asc()).all()
            context = {'songs': [song.id for song in all_songs], 'current_index': 0}

    songs = context['songs']
    idx = context.get('current_index', 0)

    # Move to next song
    if idx + 1 < len(songs):
        context['current_index'] += 1
    else:
        context['current_index'] = 0

    next_song_id = songs[context['current_index']]
    session['playback_context'] = context

    next_song = Song.query.get_or_404(next_song_id)

    return jsonify({
        'id': next_song.id,
        'name': next_song.name,
        'artist': next_song.artist_obj.name if next_song.artist_obj else "Unknown Artist",
        'album': getattr(next_song, 'album', ''),
        'lyrics': getattr(next_song, 'lyrics', 'Lyrics not available'),
        'image_url': getattr(next_song, 'image_url', '/static/default_album.png'),
        'youtube_url': next_song.youtube_url
    })





# queue previous song
@app.route('/queue/previous', methods=['GET'])
def get_previous_song():
    context = session.get('playback_context')

    # If no context, initialize from queue
    if not context:
        queue_items = QueueItem.query.filter_by(user_id=session['user_id']).order_by(QueueItem.added_at.asc()).all()
        if not queue_items:
            return jsonify({'message': 'Queue is empty'}), 404
        context = {
            'songs': [item.song_id for item in queue_items],
            'current_index': 0
        }

    songs = context['songs']
    idx = context.get('current_index', 0)

    # Move to previous song
    if idx > 0:
        context['current_index'] -= 1
    else:
        context['current_index'] = len(songs) - 1  # wrap around to last song

    prev_song_id = songs[context['current_index']]
    session['playback_context'] = context

    prev_song = Song.query.get_or_404(prev_song_id)

    return jsonify({
        'id': prev_song.id,
        'title': prev_song.name,
        'artist': prev_song.artist_obj.name if prev_song.artist_obj else "Unknown Artist",
        'url': prev_song.youtube_url
    })




# current song
@app.route('/queue/current', methods=['GET'])
def current_song():
    context = session.get('playback_context')
    if not context:
        return jsonify({'message': 'No playback context'}), 404

    idx = context.get('current_index', 0)
    song = Song.query.get(context['songs'][idx])

    return jsonify({
        'id': song.id,
        'title': song.title,
        'artist': song.artist_obj.name if song.artist_obj else song.artist,
        'url': song.youtube_url
    })
# Toggle Shuffle & Repeat
@app.route('/playback/settings', methods=['POST'])
def update_playback_settings():
    context = session.get('playback_context')
    if not context:
        return jsonify({'message': 'No playback context'}), 404

    data = request.get_json()
    context['shuffle'] = data.get('shuffle', context.get('shuffle', False))
    context['repeat'] = data.get('repeat', context.get('repeat', False))
    session['playback_context'] = context

    return jsonify({'message': 'Playback settings updated', 'shuffle': context['shuffle'], 'repeat': context['repeat']})

@app.route('/queue', methods=['POST'])
def add_to_queue():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    data = request.get_json()
    song_id = data.get('song_id')
    if not song_id:
        return jsonify({'error': 'song_id is required'}), 400

    queue_item = QueueItem(user_id=session['user_id'], song_id=song_id)
    db.session.add(queue_item)
    db.session.commit()
    return jsonify({'message': 'Song added to queue'}), 201

@app.route('/queue', methods=['GET'])
def get_queue():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    queue_items = QueueItem.query.filter_by(user_id=session['user_id']).order_by(QueueItem.added_at.asc()).all()
    songs = []
    for item in queue_items:
        song = Song.query.get(item.song_id)
        if song:
            songs.append({
                'id': song.id,
                'name': song.name,
                'artist': song.artist,
                'youtube_url': song.youtube_url,
                'image_url': song.image_url
            })
    return jsonify({'queue': songs})

@app.route('/queue/<int:song_id>', methods=['DELETE'])
def remove_from_queue(song_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    item = QueueItem.query.filter_by(user_id=session['user_id'], song_id=song_id).first()
    if not item:
        return jsonify({'error': 'Song not found in queue'}), 404

    db.session.delete(item)
    db.session.commit()
    return jsonify({'message': 'Song removed from queue'})

@app.route('/play/<int:song_id>')
def play_song(song_id):
    song = Song.query.get_or_404(song_id)

    # Get or initialize playback context
    context = session.get('playback_context', {})
    queue_song_ids = context.get('songs', [])

    if song.id not in queue_song_ids:
        queue_song_ids.append(song.id)

    context['songs'] = queue_song_ids
    context['current_index'] = queue_song_ids.index(song.id)
    session['playback_context'] = context

    return render_template('player.html',
                           title=song.name,
                           artist=song.artist_obj.name if song.artist_obj else "Unknown Artist",
                           album=song.album,
                           lyrics=song.lyrics,
                           image=song.image_url,
                           audio_url=song.youtube_url,
                           song_id=song.id)



#.....................SEARCH ARTIST




@app.route("/search/artist")
def search_artist():
    query = request.args.get("q", "").strip()
    artists = []
    error = None

    if query:
        try:
            url = f"https://saavn.dev/api/search/artists?query={query}&page=0&limit=10"
            res = requests.get(url, timeout=10)
            res.raise_for_status()
            data = res.json().get("data", {}).get("results", [])

            artists = [{
                "id": a.get("id"),
                "name": a.get("name"),
                "image": a.get("image", [{}])[0].get("link") if a.get("image") else None
            } for a in data]

        except requests.exceptions.RequestException:
            error = "Error fetching artists. Please try again later."

    return render_template("search_artist.html", artists=artists, query=query, error=error)


# ----------------- ARTIST DETAIL PAGE -----------------
@app.route("/artist/<artist_id>")
def artist_detail(artist_id):
    try:
        url = f"https://saavn.dev/api/artists?id={artist_id}"
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        data = res.json().get("data", {})

        # Songs
        songs = []
        for s in data.get("topSongs", []):
            songs.append({
                "id": s.get("id"),
                "name": s.get("name"),
                "album": s.get("album", {}).get("name"),
                "duration": s.get("duration"),
                "image": s.get("image", [{}])[-1].get("link") if s.get("image") else None,
                "audio_url": s.get("downloadUrl", [{}])[-1].get("url") if s.get("downloadUrl") else None,
                "url": s.get("url")
            })

        # Albums
        albums = []
        for a in data.get("topAlbums", []):
            albums.append({
                "id": a.get("id"),
                "name": a.get("name"),
                "url": a.get("url")
            })

        artist_info = {
            "id": artist_id,
            "name": data.get("name"),
            "image": data.get("image", [{}])[-1].get("link") if data.get("image") else None,
            "albums": albums,
            "songs": songs
        }

        # Ab template me render karenge
        return render_template("artist_detail.html", artist=artist_info)

    except Exception as e:
        # Error bhi template me show karenge
        return render_template("artist_detail.html", error=f"Error fetching artist: {str(e)}")

 
#--------------ALBUM_-----------
@app.route("/album/<album_id>")
def album_detail(album_id):
    try:
        url = f"https://saavn.dev/api/albums?id={album_id}"
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        data = res.json().get("data", {})

        songs = []
        for s in data.get("songs", []):
            songs.append({
                "id": s.get("id"),
                "name": s.get("name"),
                "duration": s.get("duration"),
                "image": s.get("image", [{}])[-1].get("link") if s.get("image") else None,
                "audio_url": s.get("downloadUrl", [{}])[-1].get("url") if s.get("downloadUrl") else None,
                "url": s.get("url")
            })

        album_info = {
            "id": album_id,
            "name": data.get("name"),
            "year": data.get("year"),
            "image": data.get("image", [{}])[-1].get("link") if data.get("image") else None,
            "songs": songs
        }
        return jsonify(album_info)
    except Exception as e:
        return jsonify({"error": str(e)}), 500




if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run()
