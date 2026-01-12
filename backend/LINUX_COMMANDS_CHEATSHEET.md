# 🐧 Linux Commands Cheat Sheet for Huzilerz Backend

> Your familiar Windows/PowerShell commands mapped to Linux for EC2 management.

---

## 🔌 Connecting to Your Server

| Action | Command |
|--------|---------|
| SSH from VS Code | Use Remote-SSH extension with `huzilerz-backend` host |
| SSH from terminal | `ssh huzilerz-backend` |
| EC2 Instance Connect | AWS Console → EC2 → Instances → Connect → EC2 Instance Connect |

---

## 📂 Navigation & Files

| Windows (PowerShell) | Linux | What it does |
|---------------------|-------|--------------|
| `cd backend` | `cd /home/ubuntu/huzilerz-backend` | Go to project folder |
| `dir` | `ls -la` | List files |
| `type file.txt` | `cat file.txt` | View file contents |
| `copy file1 file2` | `cp file1 file2` | Copy file |
| `del file.txt` | `rm file.txt` | Delete file |
| `mkdir folder` | `mkdir folder` | Create folder |
| `rmdir folder` | `rm -rf folder` | Delete folder |

---

## 🐍 Python/Django Commands

| Local Dev (Windows) | EC2 (Linux) | What it does |
|--------------------|-------------|--------------|
| `python manage.py runserver` | *(Use Gunicorn instead)* | Run dev server |
| `pip install package` | `pip install package` | Install package |
| `pip install -r requirements.txt` | `pip install -r requirements.txt` | Install all deps |
| `python manage.py makemigrations` | `python manage.py makemigrations` | Create migrations |
| `python manage.py migrate` | `python manage.py migrate` | Apply migrations |
| `python manage.py createsuperuser` | `python manage.py createsuperuser` | Create admin user |
| `python manage.py shell` | `python manage.py shell` | Django shell |
| `python manage.py collectstatic` | `python manage.py collectstatic --noinput` | Collect static files |

### ⚠️ On EC2, always activate venv first:
```bash
cd /home/ubuntu/huzilerz-backend
source venv/bin/activate
```

---

## 🚀 Service Management (systemctl)

| Action | Command |
|--------|---------|
| **Check status** | `sudo systemctl status gunicorn` |
| **Start service** | `sudo systemctl start gunicorn` |
| **Stop service** | `sudo systemctl stop gunicorn` |
| **Restart service** | `sudo systemctl restart gunicorn` |
| **Enable on boot** | `sudo systemctl enable gunicorn` |
| **Disable on boot** | `sudo systemctl disable gunicorn` |

### Your 3 Services:
```bash
# Check all 3 at once
sudo systemctl status gunicorn celery-worker celery-beat

# Restart all 3 after code changes
sudo systemctl restart gunicorn celery-worker celery-beat
```

---

## 📋 Viewing Logs (journalctl)

| Action | Command |
|--------|---------|
| View Gunicorn logs | `sudo journalctl -u gunicorn -f` |
| View Celery Worker logs | `sudo journalctl -u celery-worker -f` |
| View Celery Beat logs | `sudo journalctl -u celery-beat -f` |
| View all 3 at once | `sudo journalctl -u gunicorn -u celery-worker -u celery-beat -f` |
| View last 100 lines | `sudo journalctl -u gunicorn -n 100` |
| View since today | `sudo journalctl -u gunicorn --since today` |

> Press `Ctrl+C` to stop viewing live logs

---

## 🔄 After Code Changes (Deployment Workflow)

```bash
# 1. Navigate to project
cd /home/ubuntu/huzilerz-backend

# 2. Pull latest code from GitHub
git pull origin main

# 3. Activate virtual environment
source venv/bin/activate

# 4. Install any new dependencies
pip install -r requirements.txt

# 5. Run migrations
python manage.py migrate

# 6. Collect static files
python manage.py collectstatic --noinput

# 7. Restart all services
sudo systemctl restart gunicorn celery-worker celery-beat

# 8. Check everything is running
sudo systemctl status gunicorn celery-worker celery-beat --no-pager
```

---

## 🔧 Common Troubleshooting

| Problem | Command to Debug |
|---------|-----------------|
| Service won't start | `sudo journalctl -u gunicorn -n 50` |
| Check if port is in use | `sudo lsof -i :8000` |
| Kill stuck process | `sudo kill -9 <PID>` |
| Check memory usage | `free -h` |
| Check disk space | `df -h` |
| Check running processes | `htop` or `top` |
| Reboot instance | `sudo reboot` |

---

## 🌐 Nginx Commands

| Action | Command |
|--------|---------|
| Check config syntax | `sudo nginx -t` |
| Restart Nginx | `sudo systemctl restart nginx` |
| View Nginx error log | `sudo tail -f /var/log/nginx/error.log` |
| View Nginx access log | `sudo tail -f /var/log/nginx/access.log` |

---

## 📝 Quick Reference: Full Path

```
Project: /home/ubuntu/huzilerz-backend
Venv:    /home/ubuntu/huzilerz-backend/venv
Logs:    /home/ubuntu/huzilerz-backend/logs
```

---

## 🔑 Exit Commands

| Action | Key/Command |
|--------|-------------|
| Exit `less`/pager | `q` |
| Exit live logs | `Ctrl+C` |
| Exit SSH session | `exit` or `Ctrl+D` |
| Clear terminal | `clear` or `Ctrl+L` |
