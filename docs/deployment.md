# Deploying SusDevOS to Contabo VPS

**Target:** Contabo VPS S (4 vCPU, 8 GB RAM, 200 GB SSD NVMe, ~€5.50/month) or VPS M (8 vCPU, 16 GB RAM).
**OS:** Ubuntu 24.04 LTS.
**Domain:** susdevos.com
**Stack:** Docker Compose — Next.js + Django/Gunicorn + Celery + PostgreSQL/PostGIS + Redis + Nginx + Certbot.
**File storage:** Cloudflare R2 (free up to 10 GB/month, S3-compatible).

---

## §0 — Pre-flight

Settle these **before** you SSH in. Everything here is done in a browser, and two of the three
have propagation delays, so start them first.

### 0.1 — Point DNS away from the Namecheap parking page

The domain currently serves Namecheap's parking page. Those records must be **removed**, not
just added to — a leftover `URL Redirect` on `@` will hijack the ACME challenge and Let's
Encrypt will fail to issue.

In Namecheap → Domain List → susdevos.com → **Advanced DNS**:

**Delete these two:**

| Type | Host | Value |
|------|------|-------|
| CNAME Record | `www` | `parkingpage.namecheap.com.` |
| URL Redirect Record | `@` | `http://www.susdevos.com/` |

**Add these two:**

| Type | Host | Value | TTL |
|------|------|-------|-----|
| A Record | `@` | `<VPS IP>` | Automatic |
| A Record | `www` | `<VPS IP>` | Automatic |

Verify from your machine before continuing — both must return the VPS IP and nothing else:

```bash
dig susdevos.com +short
dig www.susdevos.com +short
```

Propagation is usually 5–30 minutes. **Do not start §3 until both resolve**, or cert issuance
will fail and you will hit Let's Encrypt's rate limit (5 failures per hostname per hour).

### 0.2 — Create the Cloudflare R2 bucket

File uploads and generated reports go to R2. Free to 10 GB with no egress charge.

1. Cloudflare dashboard → **R2** → *Create bucket* → name it `susdevos-files`, location auto.
2. **R2** → *Manage R2 API Tokens* → *Create API token*:
   - Permissions: **Object Read & Write**
   - Scope: **specify bucket** → `susdevos-files` (do not grant account-wide access)
3. Copy the **Access Key ID** and **Secret Access Key** — the secret is shown once.
4. From the bucket's *Settings* page, copy the **S3 API endpoint**. It looks like
   `https://<ACCOUNT_ID>.r2.cloudflarestorage.com`.

You now have four values for `backend/.env.prod`: `AWS_ACCESS_KEY_ID`,
`AWS_SECRET_ACCESS_KEY`, `AWS_S3_ENDPOINT_URL`, and `AWS_STORAGE_BUCKET_NAME=susdevos-files`.

### 0.3 — Transactional email

Invitations, onboarding links and password resets all send email. Without a working sender, a
new user can never set their password — so this is required for the product to function, even
though the stack will start without it.

Postmark is what `.env.prod.example` assumes: create a Server, copy its **Server API Token**,
and use that same token as **both** `EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD`. Verify the
sender signature for `noreply@susdevos.com` or Postmark will reject the send.

Any SMTP provider works — adjust `EMAIL_HOST` and `EMAIL_PORT` to match.

### 0.4 — What you need before starting, and what can wait

**Required to launch:**

| Value | Source |
|-------|--------|
| `SECRET_KEY`, `JWT_SIGNING_KEY`, `DB_PASSWORD` | Generated on the VPS — see §2 |
| `SUPERADMIN_1_PASSWORD`, `SUPERADMIN_2_PASSWORD` | Chosen by you; change after first login |
| R2 credentials ×4 | §0.2 |
| SMTP credentials | §0.3 |

**Safe to leave blank at launch** — each is guarded and degrades without breaking startup:

| Value | Effect if unset |
|-------|-----------------|
| `CLIMATIQ_API_KEY` | Weekly emission-factor sync skips; seeded factors still work |
| `COMPANIES_HOUSE_API_KEY` | Company lookup returns an error to the caller |
| `IUCN_API_KEY` | Species enrichment skips the Red List status |
| `OPEN_EXCHANGE_RATES_API_KEY` | ECB remains the only FX source; the fallback no-ops |
| `VERRA_CSV_URL` | Verra credit validation skips |
| `SENTRY_DSN` | No error reporting |

Gold Standard validation needs no key — it queries a public registry — and is a no-op until
offsets exist.

### 0.5 — Known first-deploy notes

- **The database starts empty**, so the `ecosystem/0004` foreign-key migration cannot hit the
  orphaned-row problem that would affect an existing database (see SUS-6). A fresh deploy is
  the safe time to apply it.
- **Celery beat validates its schedule at startup.** If `beat_schedule` names a task no worker
  has registered, beat exits with `ImproperlyConfigured` rather than silently publishing tasks
  nobody runs. Verified passing with all 11 scheduled tasks.
- **Reports render to R2, not local disk**, because `USE_S3=True`. Confirm the first generated
  report appears in the bucket.

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
# The repo is private — create a read-only deploy key so the VPS can pull it
ssh-keygen -t ed25519 -C "susdevos-vps-pull" -f ~/.ssh/repo_deploy -N ""
cat ~/.ssh/repo_deploy.pub
# → GitHub: Software-Lifecycle-Consultants/SusDevOS-Pro → Settings → Deploy keys
#   → Add deploy key → paste → leave "Allow write access" UNCHECKED

# Tell SSH to use that key for github.com
cat >> ~/.ssh/config << 'EOF'
Host github.com
    IdentityFile ~/.ssh/repo_deploy
    IdentitiesOnly yes
EOF

# Clone the repo (SSH — the deploy key authenticates the pull)
sudo mkdir -p /opt/susdevos
sudo chown deploy:deploy /opt/susdevos
git clone git@github.com:Software-Lifecycle-Consultants/SusDevOS-Pro.git /opt/susdevos
cd /opt/susdevos

# Generate Diffie-Hellman params (takes 2–3 minutes — run once)
openssl dhparam -out nginx/ssl/dhparam.pem 2048

# Create the production env file
cp backend/.env.prod.example backend/.env.prod
nano backend/.env.prod          # fill in all values

# (Frontend NEXT_PUBLIC_* values come from the top-level .env below — they are
#  passed to the Next.js image as Docker build args. Local frontend env files
#  are excluded from the image by frontend/.dockerignore.)
```

**Generate the three secrets on the server** — this keeps them off your laptop, out of your
shell history elsewhere, and out of any chat transcript:

```bash
cd /opt/susdevos

# Prints three values. Copy each into backend/.env.prod, then clear the terminal.
python3 - <<'PY'
import secrets, string
alphabet = string.ascii_letters + string.digits
print("SECRET_KEY="      + secrets.token_urlsafe(60))
print("JWT_SIGNING_KEY=" + secrets.token_urlsafe(60))
print("DB_PASSWORD="     + "".join(secrets.choice(alphabet) for _ in range(32)))
PY
```

`DB_PASSWORD` must be identical in **two** files — `backend/.env.prod` and the top-level
`/opt/susdevos/.env` created below. Postgres reads it from the top-level file when it
initialises its data volume on first start; if the two ever disagree, the API cannot
authenticate and the only fix is to destroy and recreate the volume.

Keep `DB_PASSWORD` alphanumeric. In a Compose `.env` file a `#` begins a comment and a `$`
begins variable interpolation — either will silently truncate or mangle the password.

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
2. `git pull --ff-only origin main`
3. Rebuilds the `api`, celery workers, and `nextjs` images
4. Runs migrations and `collectstatic` **on the new image** (one-off containers,
   before traffic switches)
5. Restarts the updated containers (DB and Redis are untouched)
6. Waits for `/health/` to respond, then reloads Nginx so it picks up the
   recreated containers' new IPs (prevents stale-upstream 502s)

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
