# Deploying SusDevOS to Contabo VPS

**Target:** Contabo VPS S (4 vCPU, 8 GB RAM, 200 GB SSD NVMe, ~€5.50/month) or VPS M (8 vCPU, 16 GB RAM).
**OS:** Ubuntu 24.04 LTS.
**Domain:** susdevos.com
**Stack:** Docker Compose — Next.js + Django/Gunicorn + Celery + PostgreSQL/PostGIS + Redis + Nginx + Certbot.
**File storage:** Cloudflare R2 (free up to 10 GB/month, S3-compatible).

---

## §1 — Provision the VPS

1. Order a VPS at contabo.com → Cloud VPS → VPS S or VPS M → Ubuntu 24.04.
2. Contabo emails root credentials — change the root password on first login.
3. Note the server IP address.

**Point DNS before doing anything else** — Let's Encrypt needs a reachable domain:

| Record | Type | Value |
|--------|------|-------|
| `susdevos.com` | A | `<VPS IP>` |
| `www.susdevos.com` | A | `<VPS IP>` |

Allow DNS to propagate (5–30 minutes). Verify: `dig susdevos.com +short`

---

## §2 — Initial server setup

SSH in as root:

```bash
# Update packages
apt-get update && apt-get upgrade -y

# Install Docker (official script)
curl -fsSL https://get.docker.com | sh

# Create a non-root deploy user
useradd -m -s /bin/bash deploy
usermod -aG docker deploy

# Copy your SSH key to deploy user
mkdir -p /home/deploy/.ssh
cp ~/.ssh/authorized_keys /home/deploy/.ssh/
chown -R deploy:deploy /home/deploy/.ssh
chmod 700 /home/deploy/.ssh && chmod 600 /home/deploy/.ssh/authorized_keys

# Harden SSH — disable root login and password auth
sed -i 's/#PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
systemctl restart ssh

# Basic firewall (keep 22 for SSH — change port later if desired)
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable
```

Log out and log back in as `deploy`.

```bash
# Clone the repo
sudo mkdir -p /opt/susdevos
sudo chown deploy:deploy /opt/susdevos
git clone https://github.com/yourorg/susdevos.git /opt/susdevos
cd /opt/susdevos

# Generate Diffie-Hellman params (takes 2–3 minutes — run once)
openssl dhparam -out nginx/ssl/dhparam.pem 2048

# Create production env files
cp backend/.env.prod.example backend/.env.prod
nano backend/.env.prod          # fill in all values
cp frontend/.env.production.example frontend/.env.production.local
nano frontend/.env.production.local   # fill in NEXT_PUBLIC_* values
```

**Required backend values before continuing:**

| Variable | How to get it |
|----------|---------------|
| `SECRET_KEY` | `python3 -c "import secrets; print(secrets.token_urlsafe(60))"` |
| `JWT_SIGNING_KEY` | Same command, different value |
| `DB_PASSWORD` | Strong random password — store safely |
| `AWS_ACCESS_KEY_ID / SECRET` | Cloudflare R2 → Manage R2 API Tokens |
| `AWS_S3_ENDPOINT_URL` | R2 bucket overview → S3 API endpoint |
| `EMAIL_HOST_USER / PASSWORD` | Postmark → Server → API Tokens |

Create the top-level `.env` file that Docker Compose reads for DB credentials shared between services:

```bash
cat > /opt/susdevos/.env << 'EOF'
DB_NAME=susdevos
DB_USER=susdevos
DB_PASSWORD=<your-db-password>           # same as in backend/.env.prod
NEXT_PUBLIC_SITE_URL=https://susdevos.com
NEXT_PUBLIC_API_URL=http://api:8000
EOF
```

---

## §3 — First-time SSL cert issuance

Nginx can't start with the HTTPS config until certs exist. Use the temporary HTTP-only config first.

```bash
cd /opt/susdevos

# Step 1: swap in the HTTP-only init config
mv nginx/conf.d/susdevos.conf nginx/conf.d/susdevos.conf.bak
cp nginx/conf.d/susdevos-init.conf nginx/conf.d/susdevos.conf

# Step 2: start Nginx on HTTP only
docker compose -f docker-compose.prod.yml up -d nginx

# Verify ACME path is reachable (should return 200)
curl -I http://susdevos.com/.well-known/acme-challenge/test

# Step 3: issue cert for apex + www
docker compose -f docker-compose.prod.yml run --rm certbot certonly \
  --webroot --webroot-path=/var/www/certbot \
  --email hello@susdevos.com \
  --agree-tos \
  --no-eff-email \
  -d susdevos.com \
  -d www.susdevos.com

# Step 4: restore the HTTPS config
rm nginx/conf.d/susdevos.conf
mv nginx/conf.d/susdevos.conf.bak nginx/conf.d/susdevos.conf

# Step 5: reload Nginx (now has valid certs)
docker compose -f docker-compose.prod.yml exec nginx nginx -s reload
```

If Certbot fails: check that port 80 is open, DNS has propagated, and the Nginx container is running.

---

## §4 — First-time application startup

```bash
cd /opt/susdevos

# Build all images (first build takes 5–10 minutes)
docker compose -f docker-compose.prod.yml build

# Start everything
docker compose -f docker-compose.prod.yml up -d

# Watch logs during startup (ctrl+c to exit)
docker compose -f docker-compose.prod.yml logs -f api nextjs

# Wait for api to be healthy, then run migrations
docker compose -f docker-compose.prod.yml exec api python manage.py migrate --no-input

# Seed required reference data
docker compose -f docker-compose.prod.yml exec api python manage.py seed_gwp
docker compose -f docker-compose.prod.yml exec api python manage.py seed_modules
docker compose -f docker-compose.prod.yml exec api python manage.py seed_plans
docker compose -f docker-compose.prod.yml exec api python manage.py seed_superadmins

# Collect Django static files (served by Nginx directly)
docker compose -f docker-compose.prod.yml exec api python manage.py collectstatic --no-input
```

**Verify the deployment:**

| URL | Expected |
|-----|---------|
| `https://susdevos.com` | Next.js homepage |
| `https://susdevos.com/api/schema/` | DRF OpenAPI schema JSON |
| `https://susdevos.com/admin/` | Django admin login |
| `https://www.susdevos.com` | Redirects → `https://susdevos.com` |

Log in to `/admin/` with `SUPERADMIN_1_EMAIL` / `SUPERADMIN_1_PASSWORD`.
**Change the superadmin passwords immediately after first login.**

---

## §5 — GitHub Actions automated deploys

Every push to `main` triggers CI (tests + build) then deploys to the VPS.

In GitHub repo → Settings → Secrets and variables → Actions, add:

| Secret | Value |
|--------|-------|
| `VPS_HOST` | VPS IP address |
| `VPS_USER` | `deploy` |
| `VPS_SSH_KEY` | Deploy user's **private** SSH key (see below) |

Generate a dedicated deploy key on the VPS:

```bash
# On the VPS, as deploy user
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/github_deploy -N ""

# Authorise the public key
cat ~/.ssh/github_deploy.pub >> ~/.ssh/authorized_keys

# Print the private key — paste this as VPS_SSH_KEY in GitHub
cat ~/.ssh/github_deploy
```

The deploy job in `.github/workflows/ci.yml` runs after tests pass. It:
1. SSHes to the VPS
2. `git pull origin main`
3. Rebuilds the `api`, celery workers, and `nextjs` images
4. Restarts the updated containers (DB and Redis are untouched)
5. Runs migrations
6. Runs `collectstatic`

---

## §6 — Automatic SSL cert renewal

Let's Encrypt certs expire every 90 days. Set up a cron job:

```bash
# On the VPS, as deploy user
crontab -e

# Add this line — runs renewal check twice daily (only renews if < 30 days remain)
0 3,15 * * * cd /opt/susdevos && docker compose -f docker-compose.prod.yml run --rm --no-deps certbot renew --quiet 2>&1 && docker compose -f docker-compose.prod.yml exec nginx nginx -s reload
```

---

## §7 — Database backups

No managed DB — backups are your responsibility.

```bash
# Manual backup
docker compose -f docker-compose.prod.yml exec -T db \
  pg_dump -U susdevos susdevos | gzip > ~/backups/susdevos_$(date +%Y%m%d_%H%M%S).sql.gz

# Automated daily backup (add to deploy user's crontab)
mkdir -p ~/backups
# In crontab -e:
0 2 * * * cd /opt/susdevos && docker compose -f docker-compose.prod.yml exec -T db pg_dump -U susdevos susdevos | gzip > ~/backups/susdevos_$(date +\%Y\%m\%d).sql.gz && find ~/backups -name "*.sql.gz" -mtime +14 -delete
```

Upload to Cloudflare R2 for offsite backup (use the `aws` CLI with `--endpoint-url`).

---

## §8 — Monitoring

**Uptime Robot (free):** uptimerobot.com → Add Monitor → HTTPS → `https://susdevos.com` and `https://susdevos.com/api/schema/` → alert by email.

**Sentry (free tier):** sentry.io → New Project → Django → paste DSN into `SENTRY_DSN` in `.env.prod`, then restart:

```bash
docker compose -f docker-compose.prod.yml up -d --no-deps api
```

**Container resource usage:**

```bash
docker stats --no-stream
df -h
docker system df
```

If the VPS S runs low on memory, upgrade to VPS M in the Contabo control panel.

---

## §9 — Operational commands

```bash
# View live logs
docker compose -f docker-compose.prod.yml logs -f api
docker compose -f docker-compose.prod.yml logs -f nextjs
docker compose -f docker-compose.prod.yml logs -f celery_worker

# Restart a single service
docker compose -f docker-compose.prod.yml restart api
docker compose -f docker-compose.prod.yml restart nextjs

# Open a Django shell
docker compose -f docker-compose.prod.yml exec api python manage.py shell

# Run a management command
docker compose -f docker-compose.prod.yml exec api python manage.py <command>

# Check all container statuses
docker compose -f docker-compose.prod.yml ps

# Restore from backup
gunzip < ~/backups/susdevos_YYYYMMDD.sql.gz | \
  docker compose -f docker-compose.prod.yml exec -T db psql -U susdevos susdevos

# Force-rebuild a specific image (e.g. after a base image update)
docker compose -f docker-compose.prod.yml build --no-cache nextjs
docker compose -f docker-compose.prod.yml up -d --no-deps nextjs

# Prune dangling images (safe to run anytime)
docker image prune -f
```
