# SusDevOS Guide for ESG Consultants — Managing Multiple Clients, Verification Workflows & White-Label Reporting

**Who this guide is for:** Sustainability consultants and ESG advisory firms managing GHG inventories and reporting for multiple client organisations. You are likely on the **Agency plan** with your consultancy as the account holder and each client as a separate Entity.

**What the Agency plan gives you:**
- Up to 25 client entities (add more at £15/entity/month)
- Unlimited users across all entities
- White-label PDF reports with your firm's branding
- Client read-only portal (clients can view their own data without accessing yours)
- Priority support (8-hour response)
- Bulk data import by CSV

---

## 1. Structuring Client Entities

Each client organisation is a separate **Entity** in SusDevOS. Entities are isolated — a client's data is never visible to another client, and your team only sees the entities you have access to.

### 1.1 Create a client entity

1. Navigate to **Entities → New Entity**.
2. Fill in the client's details:
   - **Legal name** and Companies House number (auto-populate fetches registered address and SIC codes).
   - **Consolidation approach** — confirm with the client: Equity Share, Financial Control, or Operational Control.
   - **SBTi Company ID** — if the client has an SBTi commitment, link it here for automatic registry sync.
3. **Parent/subsidiary structure** — if the client is a group, create the parent entity first, then create subsidiary entities and set the `Parent Entity` field.

### 1.2 Add your team to a client entity

Your consultants need to be users in each client entity they work on. The same email address can have separate accounts in different entities.

1. Navigate to **[Client Entity] → Settings → Users → Invite User**.
2. Set role to **Manager** for consultants who will enter and review data, or **Admin** if they need to verify inventories or manage the client's users.

> **Tip:** If you have a large team, consider creating a standard set of privilege overrides for your "Senior Consultant" and "Data Entry" profiles and applying them to each new entity rather than adjusting roles each time.

---

## 2. Parallel Client Workflows

When managing multiple clients simultaneously, the recommended workflow keeps each client's inventory progressing on their schedule.

### 2.1 Annual engagement cycle

For each client, the typical annual cycle is:

| Phase | SusDevOS actions | Typical timing |
|-------|-----------------|---------------|
| Kickoff | Create/verify entity; confirm boundary and consolidation approach | Jan–Feb |
| Data collection | Create inventory; add Scope 1/2 from client's utility bills | Feb–Apr |
| Scope 3 assessment | Complete relevance screen; enter material categories | Mar–May |
| Internal review | Review totals; flag gaps; request missing data from client | May–Jun |
| Verification prep | Submit for internal approval; share verifier read link | Jun–Jul |
| Third-party verification | Verifier reviews; mark as verified once complete | Jul–Sep |
| Reporting | Generate white-label PDF; export CDP format if required | Sep–Oct |

### 2.2 Switching between clients

Use the **Entity Switcher** in the top navigation bar. Your session context switches immediately — all data views, reports, and settings now show the selected entity.

The `X-Entity-ID` header is sent with every API request to enforce isolation. You cannot accidentally view or edit another client's data.

---

## 3. Verification Workflow for Clients

Third-party verification (your firm acting as the verifier, or supporting a client through their own verifier) is available on Professional plan and above. On Agency, it is included for all client entities.

### 3.1 Internal approval (your review step)

Before engaging a third-party verifier, your team should complete internal approval:

1. Navigate to **Emissions → Inventories → [client's inventory]**.
2. Confirm all emissions records are complete. Check for:
   - Missing Scope 3 categories flagged in the relevance assessment.
   - Scope 2 records with no market-based EF (check if client holds REGOs).
   - Any records still in Draft status (these are excluded from totals).
3. Click **Submit for Review** → **Approve** to set `VerificationStatus = 2`.

Once internally approved, the inventory is read-only. If the client asks for a change, you must reject the approval first (resets to Draft), make the edit, and reapprove.

### 3.2 Share with external verifier

SusDevOS generates a read-only verifier link for each inventory. The verifier can view all records, emission factors, calculation workings, and biogenic CO₂ breakdown without a SusDevOS account.

1. Navigate to the inventory → **Share → Generate Verifier Link**.
2. The link is time-limited (30 days by default). Copy and send to the verifier.
3. Once the verifier provides their sign-off letter, return to SusDevOS and click **Mark as Third-Party Verified** (`VerificationStatus = 3`).

> **Important:** Once third-party verified, the inventory is permanently immutable. No further edits are possible. Only a SusDevOS SuperAdmin can unlock it, and doing so creates an audit trail entry with the reason and timestamp.

### 3.3 Assurance statements in reports

The white-label PDF report includes an **Assurance Statement** section. Fill in:
- Verifier name and organisation
- Verification standard used (ISO 14064-3, ISAE 3410, or other)
- Level of assurance (Reasonable or Limited)
- Verification date

This is rendered in the report alongside the inventory totals.

---

## 4. White-Label Reports

Agency plan reports carry your firm's branding, not SusDevOS branding.

### 4.1 Set up your brand

1. Navigate to **Settings → Report Branding**.
2. Upload your logo (PNG or SVG, minimum 400px wide).
3. Set your primary colour (hex code) — used for headers and chart accents.
4. Enter your firm name, address, and contact email — shown in the report footer.

These settings apply to all client entities on your account.

### 4.2 Generate a white-label report

1. Navigate to **[Client Entity] → Reports → New Report**.
2. Select report type and inventory year.
3. Under **Branding**, confirm "Use agency branding" is selected.
4. Click **Queue Report**. Reports generate in 30–90 seconds.
5. Download the PDF. The client sees your firm's name and logo; SusDevOS is not referenced.

> **Tip:** Always generate a preview report before sharing with the client. Check that the entity name, reporting year, and scope totals match what the client expects.

### 4.3 Client portal — read-only access for clients

Rather than emailing PDFs, you can give clients direct read-only access to their own data.

1. Navigate to **[Client Entity] → Settings → Users → Invite Client**.
2. The client user gets read-only access to their entity's emissions, inventory, and reports.
3. They cannot edit anything, cannot see other entities, and cannot see your internal notes.

---

## 5. Bulk Data Import

When a client provides utility bills, meter reads, or travel data as a spreadsheet, use bulk import to avoid manual entry.

1. Navigate to **Emissions → Import → Download Template**.
2. The CSV template includes all required fields: Scope, Category, Emission Factor Set, Emission Factor Key, Quantity, Unit, Activity Date, Notes.
3. Populate the template with the client's data. Leave the `EmissionsAmount` column blank — it is calculated server-side.
4. Navigate to **Emissions → Import → Upload CSV**.
5. SusDevOS validates each row:
   - Unknown emission factor keys are flagged — fix before importing.
   - Duplicate records (same EF + date + quantity) are flagged as warnings.
6. Click **Confirm Import** to create all valid records.

> **Bulk import is available on Professional plan and above.** On Agency, it is available for all entities.

---

## 6. CDP Export for Clients

For clients with CDP disclosure obligations:

1. Navigate to **[Client Entity] → Reports → CDP Export**.
2. Select the reporting year and CDP module:
   - **C6** — Scope 1 and 2 totals, methodology disclosure
   - **C7** — Emissions breakdown by activity
   - **C10** — Scope 1 and 2 targets (SBTi)
3. Download the pre-formatted CSV. CDP field codes are mapped from SusDevOS data automatically.
4. Upload the CSV directly to CDP's Online Response System (ORS) as a question import.

> CDP export is available on Professional and above.

---

## 7. Billing and Entity Management

### 7.1 Adding client entities

1. Navigate to **Settings → Billing → Add Entity**.
2. Each entity beyond your plan limit is billed as an add-on (£15/entity/month on Agency).
3. The add-on is added to your next Stripe invoice.

### 7.2 Archiving a completed engagement

When an engagement ends, archive the client entity rather than deleting it. Archived entities retain all data, stop generating billing add-on charges, and cannot be edited.

1. Navigate to **[Client Entity] → Settings → Organisation → Archive Entity**.
2. Confirm. All users lose access immediately. Data is retained.

To reactivate an archived entity (e.g. the client returns for next year's inventory): contact support.

### 7.3 Non-profit / academic discounts

If a client is a registered charity or NGO, they may qualify for a 50% discount. Apply via the SusDevOS contact page. Once approved, the discount is applied at the entity subscription level and does not affect your agency plan pricing.

---

## 8. Quick Reference — Multi-Client Checklist

Use this checklist at the start of each annual engagement:

- [ ] Entity created with correct legal name and Companies House number
- [ ] Consolidation approach confirmed with client
- [ ] Reporting year created (new GHG inventory)
- [ ] Base year confirmed (required for SBTi target tracking)
- [ ] Your team members added as users (correct roles)
- [ ] Client read-only user invited (optional)
- [ ] Scope 3 relevance assessment completed (at least Scope 3 categories screened)
- [ ] Scope 2 EAC/REGO data requested from client
- [ ] SBTi target linked (if client is SBTi committed)
- [ ] White-label branding confirmed
