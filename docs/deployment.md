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
| A Record | `@` | `217.76.54.215` | Automatic |
| A Record | `www` | `217.76.54.215` | Automatic |

Verify from your machine before continuing — both must return `217.76.54.215` and nothing else:

```bash
dig susdevos.com +short
dig www.susdevos.com +short
```

As of 2026-08-22 the apex still resolves to `192.64.119.96` (Namecheap parking), so this change
has not been made yet. The VPS itself is reachable — SSH answers on port 22, and 80/443 are
closed because nothing is serving there yet, which is expected until §4.

Propagation is usually 5–30 minutes. **Do not start §3 until both resolve**, or cert issuance
will fail and you will hit Let's Encrypt's rate limit (5 failures per hostname per hour).

### 0.2 — Create the Cloudflare R2 bucket

File uploads and generated reports go to R2. Free to 10 GB with no egress charge.

**R2 must be activated on the account first.** It is opt-in, and Wrangler cannot do it —
attempting to create a bucket before activation fails with:

```
X [ERROR] A request to the Cloudflare API (/accounts/<ACCOUNT_ID>/r2/buckets) failed.
  Please enable R2 through the Cloudflare Dashboard. [code: 10042]
```

Code `10042` is `NotEntitled` — the account has no R2 subscription. Dashboard → **R2 Object
Storage** → *Enable R2*. Cloudflare requires a **payment method on file even for the free
tier** (10 GB storage, zero egress); at this application's volume nothing will be charged, but
the card is mandatory to activate the product.

Once activated, create the bucket with Wrangler:

```bash
npx wrangler login                              # opens a browser once
npx wrangler r2 bucket create susdevos-files
npx wrangler r2 bucket list                     # confirm it exists
```

The **API token still has to come from the dashboard** — Wrangler can create buckets but not
S3-compatible credentials:

1. Cloudflare dashboard → **R2** → *Manage R2 API Tokens* → *Create API token*
   - Permissions: **Object Read & Write**
   - Scope: **specify bucket** → `susdevos-files` (do not grant account-wide access)
2. Copy the **Access Key ID** and **Secret Access Key** — the secret is shown once.
3. The **S3 API endpoint** is `https://<ACCOUNT_ID>.r2.cloudflarestorage.com`. For this
   account that is:

   ```
   AWS_S3_ENDPOINT_URL=https://ae47f22307c7d002fefcc4d58bc4280b.r2.cloudflarestorage.com
   ```

   Confirm it on the bucket's *Settings* page rather than trusting this verbatim.

Prefer the dashboard for the whole thing? **R2** → *Create bucket* → name `susdevos-files`,
location auto — then the token steps above.

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
| `CLIMATIQ_API_KEY` | Weekly Climatiq refresh skips. The DEFRA library is unaffected — it needs no key (see §4 `import_defra_factors`) |
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

# Install YOUR public key for the deploy user.
#
# DANGER: Contabo hands you root + a PASSWORD, so root has no ~/.ssh/authorized_keys.
# Copying from it (`cp ~/.ssh/authorized_keys ...`) silently produces a deploy user with
# NO key — and the hardening two steps below then disables password auth and root login.
# That locks you out of the server entirely, recoverable only through the Contabo VNC
# console. Paste the key explicitly instead, and verify it before hardening anything.
#
# Replace the ssh-ed25519 line with the contents of your own ~/.ssh/id_ed25519.pub.
mkdir -p /home/deploy/.ssh
cat > /home/deploy/.ssh/authorized_keys << 'KEY'
ssh-ed25519 AAAA...your-actual-public-key... you@yourmachine
KEY
chown -R deploy:deploy /home/deploy/.ssh
chmod 700 /home/deploy/.ssh && chmod 600 /home/deploy/.ssh/authorized_keys

# Sanity-check the file really contains one full key line before going further.
wc -l /home/deploy/.ssh/authorized_keys     # expect: 1
```

**Now prove key login works — from a second terminal ON YOUR OWN MACHINE.**

Not another SSH hop from inside the server. Your private key lives on your laptop; the VPS has
no copy of it, so running this on the server falls back to password auth and fails with
`Permission denied` even when the key is installed perfectly. That failure tells you nothing.

Leave the root session connected, open a new local terminal, and run:

```bash
ssh deploy@217.76.54.215 'whoami'
```

It must print `deploy`. **Do not continue until it does.** While the root session stays open
you can always fix a mistake; once you harden SSH and close it, a missing key means VNC.

If it asks for a password, the key was not accepted — diagnose with:

```bash
ssh -v deploy@217.76.54.215 'whoami' 2>&1 | grep -iE "offering|accepted|denied|publickey"
```

Grant the deploy user sudo if the check above said it needs setup:

```bash
usermod -aG sudo deploy
```

**Only after key login is confirmed**, harden SSH — back in the root session:

```bash
# Harden SSH — disable root login and password auth
sed -i 's/^#\?PermitRootLogin.*/PermitRootLogin no/'            /etc/ssh/sshd_config
sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config

# Verify the config parses BEFORE restarting — a syntax error here is also a lockout
sshd -t && echo "sshd config OK"

systemctl restart ssh

# Confirm from the second terminal that deploy can still get in, BEFORE closing root.
#   ssh deploy@217.76.54.215 'echo still-in'

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

### Why these secrets live on the server, not in GitHub Secrets

Both files are gitignored (`backend/.env.prod` and `.env`), and the CI deploy step only runs
`git pull --ff-only origin main`, which never touches ignored or untracked files. **Deploys do
not overwrite them.** Fill them in once; they persist.

GitHub Secrets are for what *CI itself* needs — `VPS_HOST`, `VPS_USER`, `VPS_SSH_KEY`. The
application's runtime secrets are a different category: the containers read them on the server
at start-up, and CI never needs to see `DB_PASSWORD` or the R2 keys. Routing them through
GitHub would be strictly worse:

- **Wider blast radius.** Today a GitHub compromise costs source code and deploy access. Add
  app secrets and it also costs the database password, R2 credentials and JWT signing key.
- **Secrets on ephemeral runners.** CI would have to materialise `.env.prod` on a runner, where
  values can surface in logs, `set -x` output, or a failed-step dump.
- **No real gain.** The claimed benefit is reproducibility, but the same file still ends up at
  the same path — by a longer route with more exposure.

Generating secrets on the server (see above) means they never transit a laptop, a transcript,
or a third-party CI system.

**The real risk is that nothing backs them up.** If the VPS is lost, `.env.prod` goes with it.
Most values are regenerable, but `DB_PASSWORD` is not in any useful sense: Postgres bakes it
into the data volume at first init, so restoring a volume snapshot without the matching
password leaves a database you cannot authenticate to. Nightly backups (§7) are worthless if
you cannot open what you restore.

Once the file is complete, copy it into a password manager as a secure note:

```bash
cat /opt/susdevos/backend/.env.prod
```

The two `SUPERADMIN_*_PASSWORD` values are bootstrap-only and should be changed at first login,
after which that part of the copy is stale — everything else stays authoritative.

---

## §3 — First-time SSL cert issuance

Nginx can't start with the HTTPS config until certs exist. Use the temporary HTTP-only config first.

```bash
cd /opt/susdevos

# Step 1: swap in the HTTP-only init config
#   The init config lives in nginx/init/, NOT nginx/conf.d/ — conf.d is mounted into
#   the container and nginx loads every *.conf in it, so a second port-80 server for
#   susdevos.com there would shadow the real HTTP→HTTPS redirect.
mv nginx/conf.d/susdevos.conf nginx/conf.d/susdevos.conf.bak
cp nginx/init/susdevos-init.conf nginx/conf.d/susdevos.conf

# Step 2: start Nginx on HTTP only
#   nginx depends_on api + nextjs, so this also builds and starts them the first
#   time — expect 5–10 minutes before nginx is actually listening.
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

# Step 6: confirm conf.d holds ONLY the real config plus the shared snippet.
#   Anything else ending in .conf becomes a live server block.
ls nginx/conf.d/          # expect: proxy_params.conf  susdevos.conf  susdevos.conf.bak
docker compose -f docker-compose.prod.yml exec nginx nginx -t
```

`nginx -t` must report `syntax is ok` / `test is successful` with **no** "conflicting server
name" warnings. A conflict there means a stray `*.conf` is shadowing the real config.

Verify the redirect actually works, rather than assuming:

```bash
curl -sI http://susdevos.com | head -1     # expect: HTTP/1.1 301 Moved Permanently
curl -sI https://susdevos.com | head -1    # expect: HTTP/2 200
```

If Certbot fails: check that port 80 is open, DNS has propagated, and the Nginx container is
running. DNS is already correct as of 2026-08-23 — both names resolve to `217.76.54.215`.

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

# Emission factor library. Without these two the factor picker is empty and the
# emissions form refuses to submit — users cannot record emissions at all.
# seed_units must run first; the importer refuses to start if a unit is missing
# rather than silently dropping those factors.
docker compose -f docker-compose.prod.yml exec api python manage.py seed_units
docker compose -f docker-compose.prod.yml exec api python manage.py import_defra_factors

# Collect Django static files (served by Nginx directly)
docker compose -f docker-compose.prod.yml exec api python manage.py collectstatic --no-input
```

### Emission factors

`import_defra_factors` downloads the UK Government GHG conversion factors published by
DEFRA/DESNZ and imports the aggregate CO₂e factors — about 2,600 rows covering Scopes 1, 2
and 3. It needs **no API key**: the data is published under the Open Government Licence
v3.0, free to reuse commercially with attribution.

It resolves the download from the GOV.UK content API rather than a hard-coded link, because
the asset URL carries a content hash and changes whenever the file is revised. Override with
`--url` or `--file` for a pinned or offline import, or set `DEFRA_EF_SPREADSHEET_URL`.

```bash
# What would be imported, writing nothing
docker compose -f docker-compose.prod.yml exec api python manage.py import_defra_factors --dry-run

# A specific edition, or a pinned local copy
docker compose -f docker-compose.prod.yml exec api python manage.py import_defra_factors --year 2026
docker compose -f docker-compose.prod.yml exec api python manage.py import_defra_factors --file ./factors.xlsx
```

Re-running is safe — the import is idempotent and updates in place. A scheduled task
(`import-defra-factors-annually`) repeats it each July, after DEFRA's June publication and
the revisions that usually follow.

The Climatiq integration is a *separate, optional* path. It only refreshes rows that already
carry a `ClimatiqActivityId`, so it cannot populate an empty library and is not a substitute
for this step.

### If something 500s after §4

Three failures hit on the first real deploy. All are fixed in the repo, but they are worth
recognising because each looks like something else.

**`relation "users" does not exist` / `relation "plans" does not exist`.** Migrations were never
run. The marketing pages still render, so the site looks alive while every page that touches the
database returns 500 — a signup form that loads fine and then fails on submit. Count what is
applied:

```bash
docker compose -f docker-compose.prod.yml exec -T api \
  python manage.py showmigrations --plan | grep -c '^\[X\]'
```

Zero means §4 was skipped. Re-run `migrate`, the four seeds, then `collectstatic`.

**`PermissionError: [Errno 13] Permission denied: '/app/staticfiles/admin'` during
collectstatic.** The named volume was created root-owned while the container runs as non-root
`appuser`. Fixed in `backend/Dockerfile` for volumes created from now on; an existing volume
needs a one-off chown:

```bash
docker compose -f docker-compose.prod.yml run --rm --user root api \
  chown -R appuser:appuser /app/staticfiles
```

**502 from nginx after recreating containers.** `--force-recreate` gives `api` a new IP, and
nginx resolves upstreams once at config load, so it keeps dialling the old address. The CI
deploy script reloads nginx for this reason; manual restarts need it too:

```bash
docker compose -f docker-compose.prod.yml exec nginx nginx -s reload
```

A related one to know about: `Invalid HTTP_HOST header: 'api:8000'` in the API log, with a
`node` user agent. Next.js server-side rendering calls the API over the compose network, so
Django sees `Host: api:8000`. `api` must be in `ALLOWED_HOSTS` or the blog, sitemap and RSS
routes 400 while every browser-facing page looks perfectly healthy.

**Verify the deployment:**

| URL | Expected |
|-----|---------|
| `https://susdevos.com` | Next.js homepage |
| `https://susdevos.com/api/schema/` | `404` — developer documentation is disabled in production |
| `https://susdevos.com/api/entities/` (without a token) | `401` — authenticated API remains protected |
| `https://susdevos.com/api/entities/1/api-keys/` | `404` — customer API-key management is retired |
| `https://susdevos.com/health/` | `200` with `{"status":"ok"}` |
| `https://susdevos.com/admin/` | Django admin login |
| `https://www.susdevos.com` | Redirects → `https://susdevos.com` |

The application API remains reachable through HTTPS because the browser frontend calls it
directly. Reachability is not anonymous data access: Django's default DRF permission is
`IsAuthenticated`, protected endpoints reject missing/invalid JWTs, tenant scoping is enforced
server-side, and Nginx plus DRF apply separate rate limits. Only the explicitly public auth,
published-blog, and public-plan views bypass the default permission. The production OpenAPI,
Swagger, and ReDoc routes return `404` so they do not publish the route catalogue.
Customer API-key list, create, and revoke routes are not registered for any role. Customer API
access is not included in any plan during the PMF phase; first-party browser APIs remain active.

Do not publish container ports `3000`, `8000`, `5432`, or `6379` on the VPS. The production
Compose file deliberately uses `expose` for those services; only Nginx binds host ports 80/443.

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

**Uptime Robot (free):** uptimerobot.com → Add Monitor → HTTPS → `https://susdevos.com`
and `https://susdevos.com/health/` → alert by email. The OpenAPI/Swagger endpoints are
deliberately unavailable in production and must not be used as uptime checks.

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
