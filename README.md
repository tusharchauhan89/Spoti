# Spoti - Spotify Clone

Spoti is a music streaming web app clone built using **Flask**, **SQLAlchemy**, and the **JioSaavn API**.  
It supports user authentication, searching songs/artists, playlists, queue management, and more.

---

## Features
- User registration & login
- Search songs & artists
- Create and manage playlists
- Favorites & recently played songs
- Queue and playback controls
- Play songs with audio preview
- Artist & Album detail pages

---

## Requirements
- Python 3.10+
- Flask
- Flask-SQLAlchemy
- Flask-Migrate
- Requests
- Other dependencies in `requirements.txt`

---

## Setup Instructions

1. **Clone the repository**
```bash
git clone https://github.com/tusharchauhan89/Spoti.git
cd Spoti
---

##Create a virtual environment & activate it
python -m venv venv
venv\Scripts\activate   # For Windows
# OR
source venv/bin/activate # For Linux/Mac
pip install -r requirements.txt
python
>>> from app import db
>>> db.create_all()
>>> exit()
python app.py
http://127.0.0.1:5000/
