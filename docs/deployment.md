# Deploying SusDevOS on a Hetzner VPS

Target: Hetzner CX31 (2 vCPU, 8 GB RAM, 80 GB SSD, ~€12/month).
OS: Ubuntu 24.04 LTS.
Stack: Docker Compose (backend + DB + Redis + Nginx + Certbot). Frontend on Vercel (free tier).
File storage: Cloudflare R2 (free up to 10 GB/month).

---

## §1 — Provision the VPS

1. Create a Hetzner account at hetzner.com.
2. New Project → New Server → location: Nuremberg (or Helsinki) → Ubuntu 24.04 → CX31.
3. Add your SSH public key during setup.
4. Note the server's public IP address.

Point your DNS at the IP before doing anything else — Let's Encrypt needs a working domain to issue a cert:
- `api.yourdomain.com` → A record → `<VPS IP>`

Allow DNS to propagate (usually 5–30 minutes).

---

## §2 — Initial server setup

SSH in as root, then run:

```bash
# Update packages
apt-get update && apt-get upgrade -y

# Install Docker
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
sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
systemctl restart ssh

# Basic firewall
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

# Generate Diffie-Hellman params (takes 2–3 minutes)
openssl dhparam -out nginx/ssl/dhparam.pem 2048

# Create production env file
cp backend/.env.prod.example backend/.env.prod
nano backend/.env.prod   # fill in all values — see comments in the file
```

**Required values to fill in before continuing:**

| Variable | Where to get it |
|----------|----------------|
| `SECRET_KEY` | `python3 -c "import secrets; print(secrets.token_urlsafe(60))"` |
| `JWT_SIGNING_KEY` | Same command, different value |
| `DB_PASSWORD` | Make up a strong random password |
| `AWS_ACCESS_KEY_ID / SECRET` | Cloudflare R2 → Manage R2 API Tokens |
| `AWS_S3_ENDPOINT_URL` | R2 bucket overview — copy the S3 API endpoint |
| `EMAIL_HOST_USER / PASSWORD` | Postmark → Server → API Tokens |
| `ALLOWED_HOSTS` | `api.yourdomain.com` |
| `CORS_ALLOWED_ORIGINS` | Your Vercel URL + custom frontend domain |

Also export the DB vars for Docker Compose to read:

```bash
# Add to /home/deploy/.bashrc or /opt/susdevos/.env (sourced by compose)
export DB_NAME=susdevos
export DB_USER=susdevos
export DB_PASSWORD=<same value as in .env.prod>
```

Or set them inline — Docker Compose reads the top-level `.env` file automatically:

```bash
cat > /opt/susdevos/.env <<EOF
DB_NAME=susdevos
DB_USER=susdevos
DB_PASSWORD=<your-db-password>
EOF
```

---

## §3 — First-time SSL cert issuance

Nginx can't start with the full HTTPS config until certs exist. Use the init config first.

```bash
cd /opt/susdevos

# Step 1: Activate the HTTP-only init config
# The HTTPS config must not be active yet (nginx will fail to start without certs)
mv nginx/conf.d/susdevos.conf nginx/conf.d/susdevos.conf.https
cp nginx/conf.d/susdevos-init.conf nginx/conf.d/susdevos.conf

# Edit the domain placeholder in the init config
sed -i 's/api.yourdomain.com/api.yourdomain.com/g' nginx/conf.d/susdevos.conf   # replace with real domain

# Step 2: Start nginx on HTTP only + certbot
docker compose -f docker-compose.prod.yml up -d nginx

# Verify nginx is up and the ACME path is reachable
curl -I http://api.yourdomain.com/.well-known/acme-challenge/test

# Step 3: Issue cert
docker compose -f docker-compose.prod.yml run --rm certbot certonly \
  --webroot --webroot-path=/var/www/certbot \
  --email hello@yourdomain.com \
  --agree-tos \
  --no-eff-email \
  -d api.yourdomain.com

# Step 4: Switch to the HTTPS config
rm nginx/conf.d/susdevos.conf
mv nginx/conf.d/susdevos.conf.https nginx/conf.d/susdevos.conf

# Edit domain placeholder in the HTTPS config
sed -i 's/api.yourdomain.com/api.yourdomain.com/g' nginx/conf.d/susdevos.conf   # replace with real domain

# Step 5: Reload nginx
docker compose -f docker-compose.prod.yml exec nginx nginx -s reload
```

---

## §4 — First-time application startup

```bash
cd /opt/susdevos

# Build all images
docker compose -f docker-compose.prod.yml build

# Start everything
docker compose -f docker-compose.prod.yml up -d

# Watch logs for errors during startup
docker compose -f docker-compose.prod.yml logs -f api

# Run migrations
docker compose -f docker-compose.prod.yml exec api python manage.py migrate --no-input

# Seed reference data (required before first login)
docker compose -f docker-compose.prod.yml exec api python manage.py seed_superadmins
docker compose -f docker-compose.prod.yml exec api python manage.py seed_modules
docker compose -f docker-compose.prod.yml exec api python manage.py seed_gwp
docker compose -f docker-compose.prod.yml exec api python manage.py seed_plans

# Collect static files
docker compose -f docker-compose.prod.yml exec api python manage.py collectstatic --no-input
```

Visit `https://api.yourdomain.com/admin/` — you should see the Django admin login page.
Log in with the `SUPERADMIN_1_EMAIL` / `SUPERADMIN_1_PASSWORD` values from `.env.prod`.

**Change the superadmin passwords immediately after first login.**

---

## §5 — Connect GitHub Actions for automated deploys

Every push to `main` will now SSH into the VPS, rebuild the app image, and restart the containers (leaving DB and Redis untouched).

In your GitHub repo → Settings → Secrets and variables → Actions, add:

| Secret | Value |
|--------|-------|
| `VPS_HOST` | VPS IP address or `api.yourdomain.com` |
| `VPS_USER` | `deploy` |
| `VPS_SSH_KEY` | Contents of the deploy user's **private** SSH key |

Generate a deploy key pair on the VPS (separate from your personal key):

```bash
# On the VPS, as deploy user
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/github_deploy -N ""

# Authorise the public key for SSH login
cat ~/.ssh/github_deploy.pub >> ~/.ssh/authorized_keys

# Print the private key — paste this into the VPS_SSH_KEY GitHub secret
cat ~/.ssh/github_deploy
```

Test a deploy by pushing a commit to `main`. Watch the Actions tab in GitHub.

---

## §6 — Deploy the frontend to Vercel

The frontend (Next.js) runs on Vercel — no VPS config needed.

1. Push the repo to GitHub (if not already there).
2. vercel.com → New Project → Import from GitHub → select the repo.
3. Set the root directory to `frontend`.
4. Add environment variables:
   - `NEXT_PUBLIC_API_URL` = `https://api.yourdomain.com`
5. Deploy. Vercel auto-deploys on every push to `main`.
6. Add your custom frontend domain in the Vercel dashboard (optional).

---

## §7 — Automatic cert renewal

Let's Encrypt certs expire every 90 days. Set up a cron job on the VPS to renew automatically:

```bash
# On the VPS, as deploy user
crontab -e

# Add this line — runs renewal check twice daily (certbot only renews if < 30 days remain)
0 3,15 * * * cd /opt/susdevos && docker compose -f docker-compose.prod.yml run --rm certbot renew --quiet && docker compose -f docker-compose.prod.yml exec nginx nginx -s reload
```

---

## §8 — Database backups

No managed DB means backups are your responsibility.

```bash
# Manual backup
docker compose -f docker-compose.prod.yml exec db \
  pg_dump -U susdevos susdevos | gzip > /opt/backups/susdevos_$(date +%Y%m%d_%H%M%S).sql.gz

# Automated daily backup (add to crontab)
mkdir -p /opt/backups
crontab -e
# Add:
0 2 * * * cd /opt/susdevos && docker compose -f docker-compose.prod.yml exec -T db pg_dump -U susdevos susdevos | gzip > /opt/backups/susdevos_$(date +\%Y\%m\%d).sql.gz && find /opt/backups -name "*.sql.gz" -mtime +14 -delete
```

For offsite backup, upload to Cloudflare R2 or Hetzner Object Storage using the AWS CLI.

---

## §9 — Monitoring

**Uptime Robot (free):** uptimedrobot.com → Add Monitor → HTTP → `https://api.yourdomain.com/api/schema/` → alert by email/Slack.

**Sentry (free tier):** sentry.io → New Project → Django → copy DSN into `SENTRY_DSN` in `.env.prod`. Restart the API container:

```bash
docker compose -f docker-compose.prod.yml up -d --no-deps api
```

**Resource usage:**

```bash
# Check container memory usage
docker stats --no-stream

# Disk usage
df -h
docker system df
```

If the CX31 runs low on memory under load, upgrade to CX41 (€24/month, 16 GB RAM) via the Hetzner dashboard — takes 2 minutes with zero data loss.

---

## §10 — Useful operational commands

```bash
# View live logs for a service
docker compose -f docker-compose.prod.yml logs -f api
docker compose -f docker-compose.prod.yml logs -f celery_worker

# Restart a single service
docker compose -f docker-compose.prod.yml restart api

# Open a Django shell
docker compose -f docker-compose.prod.yml exec api python manage.py shell

# Run a management command
docker compose -f docker-compose.prod.yml exec api python manage.py <command>

# Check all container statuses
docker compose -f docker-compose.prod.yml ps

# Restore from backup
gunzip < /opt/backups/susdevos_YYYYMMDD.sql.gz | \
  docker compose -f docker-compose.prod.yml exec -T db psql -U susdevos susdevos
```
