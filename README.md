# Birthday Movie Website

## Features

- Flask backend
- Admin login
- Upload a complete birthday movie
- Optional separate background song
- Optional cover photo
- Year-wise memories
- SQLite database
- Movie and song playback
- Mobile-friendly design

## Local setup

```bash
python -m pip install -r requirements.txt
python app.py
```

Open:

```text
http://localhost:5000
```

Admin page:

```text
http://localhost:5000/login
```

Default password:

```text
Birthday@2026#M7x!
```

## Render deployment

Build command:

```bash
pip install -r requirements.txt
```

Start command:

```bash
gunicorn app:app
```

Environment variables:

```text
BIRTHDAY_ADMIN_PASSWORD=YourStrongPassword
SECRET_KEY=YourLongRandomSecretKey
```

## Upload formats

Movie: MP4, WEBM, MOV, M4V

Song: MP3, WAV, OGG, M4A

Cover: JPG, JPEG, PNG, WEBP, GIF

Important: Free hosting storage may not be permanent. Use cloud storage for permanent movie and song files.
