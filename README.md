# DMA Advanced Website

Features:
- Online admission database
- Admin panel
- Admin login
- Student login
- Notes/PDF upload section
- Video section
- Animated counters
- WhatsApp enquiry button

## Admin Login
Username:
```text
admin
```

Password:
```text
DMA@2026
```

## Run locally

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open:
```text
http://127.0.0.1:5000
```

Admin:
```text
http://127.0.0.1:5000/admin/login
```

## Render Deploy

Build Command:
```bash
pip install -r requirements.txt
```

Start Command:
```bash
gunicorn app:app
```

## Important for Render
Render free hosting may reset uploaded PDFs/videos after redeploy. For permanent storage later, use Google Drive, Cloudinary, Firebase, or AWS S3.
