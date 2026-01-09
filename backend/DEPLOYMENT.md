# Django Backend on AWS EC2: Complete Deployment Guide

This guide documents the exact steps taken to deploy the Huzilerz Django backend to an AWS EC2 instance (Ubuntu 24.04).

## 1. AWS Infrastructure Setup

### 1.1 Launch EC2 Instance
*   **OS:** Ubuntu 24.04 LTS
*   **Type:** t3.micro (Free Tier eligible)
*   **Security Group (`launch-wizard-1`):**
    *   **Inbound Rules:**
        *   SSH (22) - `0.0.0.0/0`
        *   HTTP (80) - `0.0.0.0/0`
        *   HTTPS (443) - `0.0.0.0/0`
        *   Custom TCP (8000) - `0.0.0.0/0` (Optional, only for direct Gunicorn testing)

### 1.2 SSH Access AND Initial Setup
Connect to the instance:
```bash
ssh -i "path/to/key.pem" ubuntu@<EC2_PUBLIC_IP>
```

Update system and install dependencies:
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip python3-venv nginx git postgresql-client -y
```

## 2. Project Setup on Server

### 2.1 Clone Repository
```bash
cd /home/ubuntu
git clone https://github.com/Izzycode820/backend.git huzilerz-backend
cd huzilerz-backend
```

### 2.2 Python Environment
Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn whitenoise
```

### 2.3 Environment Variables
Create the `.env` file (do NOT commit to Git):
```bash
nano .env
```
Paste your production variables (DB credentials, AWS keys, Secret Key, etc.).

## 3. Django Configuration Updates

Production-specific settings required in `settings.py` (or handled via `.env`):

### 3.1 Static Files (WhiteNoise)
Install WhiteNoise to allow Django/Gunicorn to serve static files:
```python
# settings.py
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # Add this
    # ...
]

STATIC_ROOT = BASE_DIR / 'staticfiles'
```

### 3.2 Security & Domains
```python
# settings.py
ALLOWED_HOSTS = ['<EC2_PUBLIC_IP>', 'api.huzilerz.com', 'localhost']

# CSRF Trusted Origins (Crucial for Django 4.0+)
CSRF_TRUSTED_ORIGINS = [
    'http://<EC2_PUBLIC_IP>', 
    'https://api.huzilerz.com'
]

# For Initial HTTP Testing (Disable until SSL is ready)
SECURE_SSL_REDIRECT = False 
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
```

### 3.3 Collect Static Files
```bash
python manage.py collectstatic --noinput
```

## 4. Application Server (Gunicorn)

Create a systemd service file to keep Gunicorn running: `sudo nano /etc/systemd/system/gunicorn.service`

```ini
[Unit]
Description=Gunicorn daemon for Django
After=network.target

[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/huzilerz-backend
Environment="PATH=/home/ubuntu/huzilerz-backend/venv/bin"
ExecStart=/home/ubuntu/huzilerz-backend/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 backend.wsgi:application

[Install]
WantedBy=multi-user.target
```

Start and enable Gunicorn:
```bash
sudo systemctl daemon-reload
sudo systemctl start gunicorn
sudo systemctl enable gunicorn
```

## 5. Web Server (Nginx)

Configure Nginx as a reverse proxy (Traffic Port 80 -> Gunicorn Port 8000):
`sudo nano /etc/nginx/sites-available/huzilerz`

```nginx
server {
    listen 80;
    server_name <EC2_PUBLIC_IP> api.huzilerz.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/huzilerz /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t  # Test config syntax
sudo systemctl restart nginx
```

## 6. Troubleshooting Common Issues

*   **CSRF Verification Failed (403):**
    *   **Cause:** "Secure" cookies enabled over HTTP or missing Trusted Origin.
    *   **Fix:** Add domain/IP to `CSRF_TRUSTED_ORIGINS` and disable `CSRF_COOKIE_SECURE` if testing without SSL.
*   **Redirect Loop:**
    *   **Cause:** `SECURE_SSL_REDIRECT = True` or HSTS enabled before SSL is set up.
    *   **Fix:** Set `SECURE_SSL_REDIRECT = False` in `.env/settings.py` until Certbot is run.
*   **Static Files 404:**
    *   **Cause:** Nginx/Gunicorn don't serve static files by default.
    *   **Fix:** Install `whitenoise` middleware and run `collectstatic`.

## 7. Upcoming Steps (SSL)
Once domain is pointed to the IP:
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d api.huzilerz.com
```
