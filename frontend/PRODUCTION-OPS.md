# Frontend Production Operations Guide

## 🔴 PENDING TASKS
- [ ] **REBUILD FRONTEND** - Complete rebuild to generate all prerender manifests properly
  ```bash
  cd /home/ubuntu/HUZILERZ/frontend
  rm -rf .next
  NODE_OPTIONS="--max-old-space-size=4096" npx next build
  pm2 restart huzilerz-frontend
  ```

---

## 📋 TABLE OF CONTENTS
1. [Daily Health Checks](#daily-health-checks)
2. [Deployment Workflows](#deployment-workflows)
3. [Maintenance Commands](#maintenance-commands)
4. [Troubleshooting](#troubleshooting)
5. [Emergency Procedures](#emergency-procedures)

---

## 🏥 DAILY HEALTH CHECKS

### Quick Status Check (2 minutes)
```bash
# 1. SSH into frontend instance
ssh -i ssh -i C:/S.T.E.V.E/V2/HUZILERZ/backend/aws/huzilerz-key.pem  ubuntu@3.213.99.18

# 2. Check PM2 status
pm2 status
# ✅ Status should be "online"
# ✅ Restart count (↺) should be low (< 5 per day)

# 3. Check memory usage
free -h
# ✅ Available memory should be > 200MB

# 4. Check disk space
df -h
# ✅ Usage should be < 80%

# 5. Check recent logs for errors
pm2 logs huzilerz-frontend --lines 50 --err
# ✅ Should not see repeated errors

# 6. Test frontend responds
curl -I https://www.huzilerz.com
# ✅ Should return "200 OK"
```

### Weekly Health Check (10 minutes)
```bash
# 1. Check SSL certificate expiry
sudo certbot certificates
# ✅ Should not expire within 30 days

# 2. Check for security updates
sudo apt update
sudo apt list --upgradable
# Apply if needed: sudo apt upgrade -y

# 3. Review error logs
sudo tail -100 /var/log/nginx/error.log
# Look for unusual patterns

# 4. Check PM2 logs size
du -sh ~/.pm2/logs/
# If > 100MB, rotate: pm2 flush

# 5. Verify auto-renewal is working
sudo systemctl status certbot.timer
# ✅ Should be "active (running)"
```

---

## 🚀 DEPLOYMENT WORKFLOWS

### ⚠️ STRICT RULES - NEVER BREAK THESE
1. **ALWAYS** test builds locally before deploying to EC2
2. **ALWAYS** pull latest changes before building
3. **ALWAYS** use `NODE_OPTIONS="--max-old-space-size=4096"` for builds
4. **ALWAYS** check PM2 logs after restart
5. **NEVER** commit `.env.production` or secrets to git
6. **NEVER** restart PM2 during high traffic (check analytics first)

---

### Workflow 1: Deploy Code Changes (Standard)

**On Local Machine:**
```bash
# 1. Make changes, test locally
cd c:\S.T.E.V.E\V2\HUZILERZ
pnpm dev

# 2. Commit and push
git add .
git commit -m "Description of changes"
git push origin master
```

**On EC2 Frontend Instance:**
```bash
# 3. SSH into instance
ssh -i C:/S.T.E.V.E/V2/HUZILERZ/backend/aws/huzilerz-key.pem  ubuntu@3.213.99.18

# 4. Navigate to repo
cd /home/ubuntu/HUZILERZ

# 5. Pull latest changes
git pull origin master

# 6. Install any new dependencies
cd frontend
pnpm install

#activate production mode 
NODE_ENV=production

# 7. Rebuild application
NODE_OPTIONS="--max-old-space-size=4096" npx next build

# 8. Restart PM2
pm2 restart huzilerz-frontend

# 9. Wait 10 seconds for startup
sleep 10

# 10. Check logs for errors
pm2 logs huzilerz-frontend --lines 30

# 11. Test frontend
curl http://localhost:3000
# Should return HTML

# 12. Test from browser
# Visit https://www.huzilerz.com
```

**Expected Timeline:**
- Pull + Install: 2-5 minutes
- Build: 3-5 minutes
- Restart + Verify: 1 minute
- **Total: ~10 minutes**

---

### Workflow 2: Update Environment Variables

```bash
# 1. SSH into instance
ssh -i ~/key.pem ubuntu@3.213.99.18

# 2. Edit .env.production
cd /home/ubuntu/HUZILERZ/frontend
nano .env.production

# 3. Make changes, save (Ctrl+X, Y, Enter)

# 4. Restart PM2 (no rebuild needed for env changes)
pm2 restart huzilerz-frontend

# 5. Verify new env vars loaded
pm2 logs huzilerz-frontend --lines 20
```

**⚠️ Important:** Environment variables are loaded at **runtime**, not build time (unless prefixed with `NEXT_PUBLIC_`). If you change `NEXT_PUBLIC_*` vars, you **MUST rebuild**.

---

### Workflow 3: Update Dependencies

```bash
# 1. On local machine, update package.json
cd c:\S.T.E.V.E\V2\HUZILERZ\frontend
pnpm update <package-name>
# Or update all: pnpm update

# 2. Test locally
pnpm dev

# 3. Commit and push
git add package.json pnpm-lock.yaml
git commit -m "Update dependencies: <package-name>"
git push origin master

# 4. On EC2, pull and rebuild
ssh -i ~/key.pem ubuntu@3.213.99.18
cd /home/ubuntu/HUZILERZ
git pull origin master
cd frontend
pnpm install
NODE_OPTIONS="--max-old-space-size=4096" npx next build
pm2 restart huzilerz-frontend
pm2 logs huzilerz-frontend --lines 30
```

---

### Workflow 4: Nginx Configuration Changes

```bash
# 1. Edit Nginx config
sudo nano /etc/nginx/sites-available/huzilers

# 2. Test configuration
sudo nginx -t
# ✅ Must pass before proceeding!

# 3. If test passes, reload Nginx
sudo systemctl reload nginx

# 4. Verify no errors
sudo tail -20 /var/log/nginx/error.log

# 5. Test frontend
curl -I https://www.huzilerz.com
```

**⚠️ CRITICAL:** Never restart Nginx (`systemctl restart`). Always use `reload` to avoid downtime.

---

## 🔧 MAINTENANCE COMMANDS

### PM2 Management

```bash
# View all processes
pm2 status

# View detailed info
pm2 info huzilerz-frontend

# View logs (live tail)
pm2 logs huzilerz-frontend

# View last 50 lines
pm2 logs huzilerz-frontend --lines 50

# View only errors
pm2 logs huzilerz-frontend --err

# Restart process
pm2 restart huzilerz-frontend

# Stop process (DO NOT USE unless emergency)
pm2 stop huzilerz-frontend

# Start process
pm2 start huzilerz-frontend

# Clear old logs (if logs > 100MB)
pm2 flush

# Save current PM2 state
pm2 save

# View PM2 startup command
pm2 startup
```

---

### Resource Monitoring

```bash
# Check memory usage
free -h

# Check disk space
df -h

# Check which processes use most memory
ps aux --sort=-%mem | head -10

# Check which processes use most CPU
ps aux --sort=-%cpu | head -10

# Real-time monitoring
htop
# (Press Q to quit)

# Check swap usage
swapon --show

# Check network connections
ss -tulpn | grep 3000
```

---

### Log Management

```bash
# View PM2 logs
pm2 logs huzilerz-frontend --lines 100

# View Nginx access logs
sudo tail -100 /var/log/nginx/access.log

# View Nginx error logs
sudo tail -100 /var/log/nginx/error.log

# Search Nginx logs for specific IP
grep "123.45.67.89" /var/log/nginx/access.log

# Search for 500 errors
grep " 500 " /var/log/nginx/access.log

# Count requests per hour (last 24h)
cat /var/log/nginx/access.log | awk '{print $4}' | cut -d: -f1,2 | sort | uniq -c

# Clear PM2 logs (use when logs > 100MB)
pm2 flush
```

---

### SSL Certificate Management

```bash
# Check certificate status
sudo certbot certificates

# Renew certificates manually (auto-renewal runs daily)
sudo certbot renew

# Test auto-renewal
sudo certbot renew --dry-run

# Check auto-renewal timer
sudo systemctl status certbot.timer

# View certificate expiry date
echo | openssl s_client -servername www.huzilerz.com -connect www.huzilerz.com:443 2>/dev/null | openssl x509 -noout -dates
```

---

### Git Operations

```bash
# Check current status
git status

# Pull latest changes
git pull origin master

# View recent commits
git log --oneline -10

# Discard local changes (⚠️ DESTRUCTIVE)
git reset --hard origin/master

# View what changed in last commit
git show HEAD

# Check current branch
git branch
```

---

## 🔥 TROUBLESHOOTING

### Issue: Frontend Returns 502/504 Gateway Timeout

**Symptoms:**
- Browser shows "502 Bad Gateway" or "504 Gateway Timeout"
- Nginx error log shows "upstream timed out"

**Diagnosis:**
```bash
# Check if PM2 is running
pm2 status
# If "stopped" or "errored", continue below

# Check if port 3000 is listening
ss -tulpn | grep 3000
# If nothing returned, Next.js is not running

# Check PM2 logs for crash reason
pm2 logs huzilerz-frontend --lines 100 --err
```

**Solution:**
```bash
# Restart PM2
pm2 restart huzilerz-frontend

# Wait 10 seconds
sleep 10

# Check logs
pm2 logs huzilerz-frontend --lines 20

# If still failing, rebuild
cd /home/ubuntu/HUZILERZ/frontend
NODE_OPTIONS="--max-old-space-size=4096" npx next build
pm2 restart huzilerz-frontend
```

---

### Issue: High Memory Usage / Server Running Slow

**Diagnosis:**
```bash
# Check memory
free -h

# Check what's using memory
ps aux --sort=-%mem | head -10

# Check swap usage
swapon --show
```

**Solution:**
```bash
# If Next.js is using > 1GB, restart PM2
pm2 restart huzilerz-frontend

# If swap is > 50% full, reboot instance (during low traffic)
sudo reboot now
# Wait 2 minutes, then SSH back in and verify PM2 restarted:
pm2 status
```

---

### Issue: SSL Certificate Expired

**Symptoms:**
- Browser shows "Your connection is not private"
- Certificate error in browser

**Solution:**
```bash
# Renew certificate
sudo certbot renew --force-renewal

# Reload Nginx
sudo systemctl reload nginx

# Test
curl -I https://www.huzilerz.com
```

---

### Issue: Can't SSH Into Instance

**Diagnosis:**
- Check if instance is running in AWS Console
- Check security group allows SSH from your IP

**Solution:**
```bash
# Update security group in AWS Console:
# EC2 → Security Groups → huzilerz-frontend-sg
# Edit inbound rules → SSH → Change source to "My IP"

# Or use EC2 Instance Connect from AWS Console
```

---

### Issue: Disk Full

**Diagnosis:**
```bash
df -h
# If / is > 90%, continue
```

**Solution:**
```bash
# Check largest directories
du -h /home/ubuntu --max-depth=2 | sort -hr | head -20

# Clear PM2 logs
pm2 flush

# Clear old builds (⚠️ Use with caution)
cd /home/ubuntu/HUZILERZ/frontend
rm -rf .next/cache

# Clear apt cache
sudo apt clean

# Check again
df -h
```

---

## 🚨 EMERGENCY PROCEDURES

### Emergency: Site is Down

**Priority: Restore service ASAP**

```bash
# 1. Check if PM2 is running
pm2 status

# 2. If stopped, restart immediately
pm2 restart huzilerz-frontend

# 3. If that fails, start PM2
pm2 start huzilerz-frontend

# 4. Check Nginx status
sudo systemctl status nginx

# 5. If Nginx is down, start it
sudo systemctl start nginx

# 6. Verify site is up
curl -I https://www.huzilerz.com

# 7. Check logs for root cause
pm2 logs huzilerz-frontend --lines 100
sudo tail -100 /var/log/nginx/error.log
```

---

### Emergency: Rollback Deployment

**If new deployment broke the site:**

```bash
# 1. SSH into instance
ssh -i ~/key.pem ubuntu@3.213.99.18

# 2. Navigate to repo
cd /home/ubuntu/HUZILERZ

# 3. View recent commits
git log --oneline -5

# 4. Reset to previous commit (⚠️ DESTRUCTIVE)
git reset --hard HEAD~1
# OR reset to specific commit:
# git reset --hard <commit-hash>

# 5. Rebuild
cd frontend
NODE_OPTIONS="--max-old-space-size=4096" npx next build

# 6. Restart
pm2 restart huzilerz-frontend

# 7. Verify site works
curl https://www.huzilerz.com
```

---

### Emergency: Database Connection Issues

**Symptoms:**
- API calls fail with 500 errors
- "Database connection failed" in logs

**Solution:**
```bash
# 1. Check if backend is running
curl https://api.huzilerz.com/api/health
# Should return 200

# 2. If backend is down, check backend instance
# (See backend ops guide)

# 3. Verify .env.production has correct API URL
cd /home/ubuntu/HUZILERZ/frontend
cat .env.production | grep API_URL
# Should show: NEXT_PUBLIC_API_URL=https://api.huzilerz.com

# 4. Restart frontend
pm2 restart huzilerz-frontend
```

---

## 📊 PERFORMANCE MONITORING

### Check Response Times

```bash
# Test frontend response time
time curl -s https://www.huzilerz.com > /dev/null

# Test API response time
time curl -s https://api.huzilerz.com/api/health > /dev/null

# Check Nginx access log for slow requests (> 1s)
awk '$NF > 1.0' /var/log/nginx/access.log | tail -20
```

---

### Monitor Real-Time Traffic

```bash
# Watch access log live
sudo tail -f /var/log/nginx/access.log

# Count requests per minute (live)
sudo tail -f /var/log/nginx/access.log | pv -l -i 60 > /dev/null
```

---

## 🔄 AUTOMATION TASKS

### Set Up Automated Health Checks (Optional)

```bash
# Create health check script
nano ~/health-check.sh
```

Paste:
```bash
#!/bin/bash
# Frontend Health Check
STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://www.huzilerz.com)
if [ "$STATUS" != "200" ]; then
    echo "Frontend down! Status: $STATUS" | logger -t frontend-health
    pm2 restart huzilerz-frontend
fi
```

```bash
# Make executable
chmod +x ~/health-check.sh

# Add to crontab (runs every 5 minutes)
crontab -e
# Add this line:
*/5 * * * * /home/ubuntu/health-check.sh
```

---

## 📝 IMPORTANT FILES & LOCATIONS

### Configuration Files
```
/etc/nginx/nginx.conf                    - Main Nginx config
/etc/nginx/sites-available/huzilers      - Frontend site config
/home/ubuntu/HUZILERZ/frontend/.env.production - Production env vars
/home/ubuntu/HUZILERZ/frontend/next.config.ts  - Next.js config
```

### Log Files
```
~/.pm2/logs/huzilerz-frontend-out.log    - PM2 stdout logs
~/.pm2/logs/huzilerz-frontend-error.log  - PM2 error logs
/var/log/nginx/access.log                - Nginx access logs
/var/log/nginx/error.log                 - Nginx error logs
```

### SSL Certificates
```
/etc/letsencrypt/live/www.huzilerz.com/fullchain.pem  - SSL cert
/etc/letsencrypt/live/www.huzilerz.com/privkey.pem    - Private key
```

---

## 🎯 QUICK REFERENCE COMMANDS

```bash
# Restart everything
pm2 restart huzilerz-frontend && sudo systemctl reload nginx

# View all logs
pm2 logs huzilerz-frontend & sudo tail -f /var/log/nginx/error.log

# Full status check
pm2 status && free -h && df -h && sudo systemctl status nginx

# Emergency rebuild
cd /home/ubuntu/HUZILERZ/frontend && rm -rf .next && NODE_OPTIONS="--max-old-space-size=4096" npx next build && pm2 restart huzilerz-frontend

# Test site
curl -I https://www.huzilerz.com && curl -I https://huzilerz.com
```

---

## 📞 ESCALATION

If all else fails:
1. Check AWS Console for instance issues
2. Review GitHub commits for recent changes
3. Check backend status (frontend depends on backend API)
4. Consider rolling back to last known good commit

---

**Last Updated:** 2026-01-13
**Instance IP:** 3.213.99.18
**Domains:** www.huzilerz.com, huzilerz.com
**Backend API:** https://api.huzilerz.com
