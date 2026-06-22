# SusDevOS Admin Guide — Organisation Setup, User Management & Compliance

**Who this guide is for:** The Admin role. You are the primary account holder for your organisation's SusDevOS instance — you set up entities, invite users, verify emissions inventories, and manage compliance settings. You have full CRUD access to all modules within your entity.

**What Admins can do that Managers and Staff cannot:**
- Verify a GHG inventory (set VerificationStatus → 2)
- Manage users and assign roles
- Manage entity settings and API keys
- View the audit log
- Delete records (soft-delete)

---

## 1. Setting Up Your Organisation

### 1.1 Create your Entity

An **Entity** is the top-level organisational boundary in SusDevOS. All data — emissions, projects, users — belongs to exactly one entity. If you operate multiple subsidiaries, each gets its own entity record.

1. Log in with your Admin account.
2. Navigate to **Settings → Organisation**.
3. Click **Edit Organisation** and fill in:
   - **Legal name** — as it appears on Companies House (UK) or your incorporation documents.
   - **Companies House Number** — if UK-registered, enter this and click **Auto-populate**. SusDevOS fetches the registered address, SIC codes, and incorporation date from the Companies House API.
   - **Industry / SIC codes** — used to suggest relevant Scope 3 categories.
   - **Consolidation approach** — choose Equity Share, Financial Control, or Operational Control (GHG Protocol, §3). This determines which subsidiaries' emissions you must include.
   - **Parent Entity** — if your organisation is a subsidiary of a parent also in SusDevOS, link it here.
4. Click **Save**.

### 1.2 Connect to SBTi (optional)

If your organisation has an SBTi commitment:

1. Navigate to **Settings → SBTi**.
2. Enter your **SBTi Company ID** (found on the SBTi Companies Taking Action page).
3. SusDevOS will match your entity to the SBTi registry and sync your commitment status, target type, and deadlines monthly.

---

## 2. Inviting and Managing Users

### 2.1 Role overview

| Role | What they can do |
|------|----------------|
| **Admin** | Full CRUD + verify inventories + manage users + view audit log |
| **Manager** | Full CRUD on all data modules; cannot verify; can invite Staff |
| **Staff** | CRUD on projects, land, ecosystem, emissions; read-only on reports |

One user = one role. Privilege overrides allow you to grant or revoke individual permissions without changing the role (see §2.3).

### 2.2 Invite a user

1. Navigate to **Settings → Users → Invite User**.
2. Enter the user's email address and select their role.
3. Click **Send Invitation**.

SusDevOS emails the user an onboarding link. The link is single-use and expires in 72 hours. The user sets their own password on first login (`/onboard`).

To resend an invitation: find the user in the list, click the three-dot menu → **Resend Invite**.

### 2.3 Privilege overrides

If a Manager needs to verify inventories without being promoted to Admin:

1. Navigate to **Settings → Users** and click the user.
2. Click **Manage Privileges**.
3. Find the **Emissions → Verify Emissions Record** interface and set the override to **Grant**.
4. Click **Save**.

Overrides are stored per-user and survive role changes. The audit log records every change.

### 2.4 Remove a user

Users are soft-deleted: their account is deactivated and all historical data they created is retained.

1. Find the user in **Settings → Users**.
2. Click the three-dot menu → **Deactivate**.
3. Confirm. The user's session is immediately invalidated.

---

## 3. Verifying a GHG Inventory

Verification is a two-stage process: internal review (set by Admin) and optional third-party sign-off (Professional plan and above).

### 3.1 Internal review workflow

1. Navigate to **Emissions → Inventories**.
2. Find the inventory you want to review (filter by Reporting Year).
3. Check that all required fields are complete — scope totals should populate automatically once all emissions records are entered.
4. Click **Submit for Review**. This sets `VerificationStatus = 1` (Submitted).
5. Review the summary page. Check:
   - Scope 1, 2 (location-based), 2 (market-based), and Scope 3 totals.
   - Biogenic CO₂ is shown separately — it is **not** included in the GWP total. This is correct GHG Protocol behaviour.
   - Any emissions records with missing emission factors are flagged in red.
6. If satisfied, click **Approve**. This sets `VerificationStatus = 2` (Internally Approved).

Once approved, the inventory becomes read-only. No emissions records can be added, edited, or deleted.

### 3.2 Third-party verification (Professional plan+)

1. After internal approval, click **Request Third-Party Verification**.
2. Share the read-only verifier link with your external verifier. They can review all records without a SusDevOS account.
3. When the verifier confirms, click **Mark as Third-Party Verified**. This sets `VerificationStatus = 3` (Verified).

At `VerificationStatus ≥ 3`, the inventory is permanently immutable. Only a SuperAdmin can unlock it (with a mandatory reason, which is written to the audit log).

### 3.3 What gets locked

Once verified:
- All `EmissionsData` records linked to this inventory: PATCH and DELETE blocked (HTTP 403).
- The `GHGInventory` record itself: PATCH and DELETE blocked.
- The Celery task `recompute_stale_inventory_totals` skips verified inventories.

---

## 4. Managing API Keys

API keys allow integrations (e.g. IoT sensors, ERP systems, third-party tools) to push data to SusDevOS without a user login.

1. Navigate to **Settings → API Keys**.
2. Click **Generate New Key**. Give it a descriptive name (e.g. "Building Energy Meters").
3. Copy the key immediately — it is shown only once.
4. The key authenticates as your entity. It is subject to the same `entity_id` scoping as user requests.

To revoke a key: find it in the list and click **Revoke**. It is immediately invalidated.

API keys do not expire automatically. Rotate them regularly and immediately on suspected compromise.

---

## 5. Audit Log

The audit log records all significant actions: user invitations, role changes, privilege overrides, inventory verifications, unlocks, and data access by SuperAdmins.

1. Navigate to **Settings → Audit Log**.
2. Filter by date range, action type, or user.

**Retention:**
| Plan | Retention |
|------|-----------|
| Free / Starter | 30 days |
| Professional / Agency | 1 year |
| Enterprise | 7 years |

Purging is automatic. If you need to export audit records before retention expires, use the **Export CSV** button.

---

## 6. Subscription and Billing

1. Navigate to **Settings → Billing**.
2. Your current plan, next billing date, and entity count are shown.
3. To upgrade: click **Change Plan** → select the tier → enter payment details via Stripe.
4. To add entities (Professional and Agency plans): click **Add Entity** — you are billed the add-on rate (£25/entity/month for Professional, £15 for Agency).

**Annual billing:** Switch to annual from the billing page for a 20% discount. Stripe prorates the remaining monthly period as a credit.

**Trial:** If you're on a 14-day trial, the days remaining are shown. Add a card before the trial expires to avoid reverting to Free. Your data is always retained.

---

## 7. Common Admin Tasks — Quick Reference

| Task | Where to find it |
|------|----------------|
| Change organisation name | Settings → Organisation → Edit |
| Invite a user | Settings → Users → Invite User |
| Change a user's role | Settings → Users → [user] → Edit Role |
| Override a single privilege | Settings → Users → [user] → Manage Privileges |
| Verify an inventory | Emissions → Inventories → [inventory] → Approve |
| Generate an API key | Settings → API Keys → Generate New Key |
| Export audit log | Settings → Audit Log → Export CSV |
| View billing | Settings → Billing |
| Add another entity | Settings → Billing → Add Entity |
