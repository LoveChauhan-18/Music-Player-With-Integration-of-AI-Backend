# Music Player With Integration of AI — Backend 🎵⚙️

Django REST Framework backend for the **Love Music Player** — an AI-powered music streaming app.

## 🗂️ Project Structure

```
backend/
├── config/               # Django project settings & URL routing
├── core/                 # Main app: Songs, AI mood detection, YouTube resolver
│   ├── models.py         # Song, Playlist, Cache models
│   ├── views.py          # API endpoints
│   ├── serializers.py    # DRF serializers
│   ├── urls.py           # Route definitions
│   └── utils/
│       └── youtube_resolver.py  # yt-dlp based full audio stream resolver
├── users/                # Authentication & user management
├── manage.py
├── requirements.txt
└── test_resolver.py      # Quick test for YouTube resolver
```

## 🔗 Repositories

| Part | Repository |
|------|-----------|
| 🖥️ **Full Project** | [Music-Player-With-Integration-of-AI](https://github.com/LoveChauhan-18/Music-Player-With-Integration-of-AI) |
| 🎨 **Frontend** | [Music-Player-With-Integration-of-AI-Frontend](https://github.com/LoveChauhan-18/Music-Player-With-Integration-of-AI-Frontend) |
| ⚙️ **Backend** | [Music-Player-With-Integration-of-AI-Backend](https://github.com/LoveChauhan-18/Music-Player-With-Integration-of-AI-Backend) |

## 🚀 Tech Stack

- **Framework:** Django 4.x + Django REST Framework
- **Database:** PostgreSQL
- **Audio:** `yt-dlp` for full-song YouTube audio resolution
- **Music Metadata:** iTunes Search API
- **Auth:** Django sessions / Token auth

## ⚙️ Getting Started

### 1. Clone the repo
```bash
git clone https://github.com/LoveChauhan-18/Music-Player-With-Integration-of-AI-Backend.git
cd Music-Player-With-Integration-of-AI-Backend
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up the database
```bash
python manage.py migrate
```

### 4. Run the development server
```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000/api/`

## 🎵 Key API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/songs/` | GET | List all songs |
| `/api/songs/search/` | GET | Search songs |
| `/api/songs/stream/<id>/` | GET | Get full audio stream URL |
| `/api/songs/mood/` | POST | AI mood-based recommendations |
| `/api/auth/login/` | POST | User login |
| `/api/auth/register/` | POST | User registration |
