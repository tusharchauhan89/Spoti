// =======================
// ELEMENTS
// =======================
const audio = document.getElementById('audio');
const playBtn = document.getElementById('playBtn');
const playIcon = document.getElementById('playIcon');
const progress = document.getElementById('progress');
const topRange = document.getElementById('top-range');
const topCurrent = document.getElementById('top-current');
const topDuration = document.getElementById('top-duration');
const volume = document.getElementById('volume');
const shuffleBtn = document.getElementById('shuffleBtn');
const repeatBtn = document.getElementById('repeatBtn');
const prevBtn = document.getElementById('prevBtn');
const nextBtn = document.getElementById('nextBtn');

// =======================
// QUEUE & STATE
// =======================
let currentQueue = []; // Array of songs
let currentIndex = 0; // Current song index
let isShuffle = false;
let isRepeat = false;

// =======================
// HELPERS
// =======================
function setProgressUI(percent) {
    progress.value = percent;
    topRange.value = percent;
}

function formatTime(t) {
    if (!t || isNaN(t)) return "0:00";
    const m = Math.floor(t / 60);
    const s = Math.floor(t % 60);
    return m + ":" + (s < 10 ? '0' + s : s);
}

// =======================
// LOAD SONG TO FRONTEND
// =======================
function loadSongFrontend(song, index = null) {
    if (!song) return;
    if (index !== null) currentIndex = index;

    document.getElementById('song-title').innerText = song.name || '';
    document.getElementById('song-artist').innerText = song.artist || '';
    document.getElementById('song-album').innerText = song.album || '';
    document.getElementById('song-lyrics').innerText = song.lyrics || 'Lyrics not available';
    document.getElementById('song-image').src = song.image_url || '/static/default_album.png';
    document.getElementById('bottom-song-image').src = song.image_url || '/static/default_album.png';
    document.getElementById('bottom-song-title').innerText = song.name || '';
    document.getElementById('bottom-song-artist').innerText = song.artist || '';

    if (song.youtube_url) {
        audio.src = song.youtube_url; // Must be playable URL
        audio.load();
        audio.play();
    }
}

// =======================
// PLAY / PAUSE
// =======================
playBtn.addEventListener('click', () => {
    if (audio.paused) {
        audio.play();
    } else {
        audio.pause();
    }
});

audio.addEventListener('play', () => playIcon.className = 'fas fa-pause');
audio.addEventListener('pause', () => playIcon.className = 'fas fa-play');

// =======================
// TIME UPDATE / SEEK
// =======================
audio.addEventListener('timeupdate', () => {
    if (audio.duration) {
        const percent = (audio.currentTime / audio.duration) * 100;
        setProgressUI(percent);
        topCurrent.textContent = formatTime(audio.currentTime);
        topDuration.textContent = formatTime(audio.duration);
    }
});

function updateAudioTime(e) {
    if (audio.duration) {
        audio.currentTime = (e.target.value / 100) * audio.duration;
    }
}

progress.addEventListener('input', updateAudioTime);
topRange.addEventListener('input', updateAudioTime);

// =======================
// VOLUME CONTROL
// =======================
volume.addEventListener('input', () => audio.volume = volume.value / 100);

// =======================
// PREVIOUS / NEXT
// =======================
function playNextSong() {
    if (isRepeat) {
        loadSongFrontend(currentQueue[currentIndex], currentIndex);
        return;
    }

    if (isShuffle) {
        currentIndex = Math.floor(Math.random() * currentQueue.length);
        loadSongFrontend(currentQueue[currentIndex], currentIndex);
        return;
    }

    if (currentIndex + 1 < currentQueue.length) {
        currentIndex += 1;
        loadSongFrontend(currentQueue[currentIndex], currentIndex);
    } else {
        // Queue finished
        console.log("End of queue");
    }
}

function playPrevSong() {
    if (currentIndex > 0) {
        currentIndex -= 1;
        loadSongFrontend(currentQueue[currentIndex], currentIndex);
    }
}

prevBtn.addEventListener('click', playPrevSong);
nextBtn.addEventListener('click', playNextSong);

// =======================
// AUTO-PLAY NEXT SONG
// =======================
audio.addEventListener('ended', playNextSong);

// =======================
// SHUFFLE / REPEAT TOGGLE
// =======================
shuffleBtn.addEventListener('click', () => {
    isShuffle = !isShuffle;
    shuffleBtn.classList.toggle('active', isShuffle);
});

repeatBtn.addEventListener('click', () => {
    isRepeat = !isRepeat;
    repeatBtn.classList.toggle('active', isRepeat);
});

// =======================
// PLAYLIST FORM
// =======================
const playlistForm = document.getElementById('addToPlaylistForm');
if (playlistForm) {
    playlistForm.addEventListener('submit', e => {
        const select = document.getElementById('playlistSelect');
        if (!select || !select.value) {
            e.preventDefault();
            alert('Select a playlist first!');
        } else {
            playlistForm.action = `/playlists/${select.value}/add`;
        }
    });
}

// =======================
// INIT QUEUE FROM SEARCH
// =======================
function initQueueFromSearch(queue) {
    if (!Array.isArray(queue) || queue.length === 0) return;
    currentQueue = queue;
    currentIndex = 0;
}

// =======================
// AUTO-LOAD SONG ON PAGE LOAD
// =======================
window.addEventListener('load', () => {
    if (typeof searchQueue !== "undefined" && searchQueue.length > 0) {
        initQueueFromSearch(searchQueue);
        loadSongFrontend(currentQueue[0], 0); // auto-play first song
    }
});
const bottomFavBtn = document.getElementById("bottom-favorite-btn");

if (bottomFavBtn) {
    bottomFavBtn.addEventListener("click", () => {
        const songId = bottomFavBtn.dataset.songId;
        const icon = bottomFavBtn.querySelector("i");

        console.log("Clicked fav button:", songId); // debug

        if (!songId) {
            alert("No current song playing");
            return;
        }

        fetch("/toggle_favorite", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ song_id: songId })
            })
            .then(res => res.json())
            .then(data => {
                console.log("Server response:", data); // debug
                if (data.status === "added") {
                    icon.classList.remove("far");
                    icon.classList.add("fas");
                } else if (data.status === "removed") {
                    icon.classList.remove("fas");
                    icon.classList.add("far");
                }
            })
            .catch(err => console.error("Fetch error:", err));
    });
}
document.querySelectorAll(".removeBtn").forEach((btn) => {
    btn.addEventListener("click", async(e) => {
        const card = e.target.closest(".song-card");
        const songId = card.dataset.id;

        try {
            let res = await fetch(`/remove_favorite/${songId}`, { method: "POST" });
            if (res.ok) {
                card.remove(); // frontend se turant remove
            } else {
                alert("Error removing song!");
            }
        } catch (err) {
            console.error(err);
        }
    });
});