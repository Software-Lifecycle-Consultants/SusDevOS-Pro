# Data Privacy & Protection Compliance — SusDevOS

---

## Overview

SusDevOS processes two distinct categories of data with different regulatory implications:

**Business operational data** — GHG emissions figures, activity data (fuel consumption, energy use), financial spend, land parcel geometry, project data. This is not personal data in most cases but may be commercially sensitive and subject to data protection agreements.

**Personal data** — user accounts (name, email, IP address, login history), employee commuting survey responses (if collected), named business travel records, audit log entries containing user identity. This is personal data and fully in scope for GDPR, CCPA, and equivalent laws.

The distinction matters: emissions data itself is largely business-to-business and much of it is publicly disclosed anyway (CDP, CSRD, annual reports). But the user data that operates the platform, and any employee-level data used to calculate Scope 3 Category 7 (Employee Commuting), is clearly personal.

---

## 1. UK GDPR and EU GDPR

### Applicability

**UK GDPR** (UK Data Protection Act 2018 as amended post-Brexit) applies because:
- SusDevOS is likely established in the UK, or
- It processes personal data of UK data subjects regardless of where it's hosted

**EU GDPR** applies if:
- Any EU-based customers' employees use the platform (very likely)
- The platform monitors behaviour of EU data subjects

Both apply simultaneously for most realistic scenarios. The requirements are nearly identical — UK GDPR diverges mainly in the regulatory authority (ICO vs national EU DPAs).

### Data Controller vs Data Processor

SusDevOS is a **data processor** for its customers' emissions and employee data — customers determine the purpose and means of processing. SusDevOS is a **data controller** for user account data (it decides how to manage logins, sessions, audit logs).

This distinction determines responsibility:
- For personal data customers upload (e.g. named employee travel records) — SusDevOS processes under instruction; customer bears primary controller responsibility
- For user accounts, IP logs, authentication data — SusDevOS is the controller

### Lawful bases

| Data type | Lawful basis | Notes |
|-----------|-------------|-------|
| User account data | Contract (Article 6(1)(b)) | Necessary to provide the service |
| Audit logs | Legitimate interest (6(1)(f)) | Security, fraud prevention, regulatory compliance |
| Marketing emails to leads | Consent (6(1)(a)) | Opt-in at lead capture; unsubscribe in every email |
| Marketing emails to customers | Legitimate interest (6(1)(f)) | Soft opt-in for existing customers; always opt-out available |
| Employee commuting data | Contract + customer's lawful basis | Processor — customer must establish their own basis |
| Error/crash logs (Sentry) | Legitimate interest | Must be configured to strip personal data where possible |

### Data subject rights — implementation

GDPR grants rights to individuals. Each must be fulfilled within 30 days.

**Right of access (Article 15):** Users can request all personal data held about them.
- Implementation: `GET /api/users/me/data-export/` — returns JSON of user record, login history from audit log (last 12 months), notification history. Triggers a Celery task that generates a ZIP and emails a download link.

**Right to erasure (Article 17):** "Right to be forgotten."
- Implementation: `DELETE /api/users/me/` — anonymises the user record rather than hard-deleting (to preserve audit log integrity). Sets `Users.DeletedAt`, replaces name with `[Deleted User]` and email with `deleted_{hash}@redacted.invalid`. Audit log entries retain the `ChangedByUsername` snapshot but FK is nulled.
- Exception: audit log entries for verified GHG inventories must be retained for the `RetentionTier` period regardless of erasure request (legitimate interest: regulatory compliance, fraud prevention).

**Right to rectification (Article 16):** Standard account update endpoints already satisfy this.

**Right to data portability (Article 20):** The data export endpoint (access request) covers this. Format: JSON (machine-readable). GDPR requires this only for data provided by the subject on a consent or contract basis.

**Right to object (Article 21):** Applies to legitimate interest processing (marketing emails, audit logs). Opt-out of marketing emails via unsubscribe link. Objecting to audit log processing should be handled case by case — contact DPO.

### Data Processing Agreement (DPA)

Required under GDPR Article 28 whenever a controller uses a processor. SusDevOS (as processor) must offer a signed DPA to all customers.

The DPA must cover:
- Subject matter and duration of processing
- Nature and purpose of processing
- Type of personal data (user data, employee commuting data if applicable)
- Categories of data subjects (employees, contractors)
- Obligations and rights of the controller
- Sub-processors list (AWS/Hosting, Stripe, Sentry, Climatiq, etc.)
- International transfers (Standard Contractual Clauses if transferring outside UK/EEA)
- Security measures (encryption at rest, TLS, access controls)
- Breach notification commitment (inform controller within 24 hours of becoming aware)
- Return/deletion of data on termination

**Available at:** `/legal/dpa` as a downloadable PDF. Enterprise customers sign via DocuSign before onboarding.

**Standard Contractual Clauses (SCCs):** Required for any transfer of EU personal data to a country without an adequacy decision. If hosted in US (AWS us-east): use EU SCCs (Module 2: controller to processor). If hosted in UK for EU customers: use IDTA (International Data Transfer Agreement) approved by ICO.

### ICO Registration

Required in the UK for any organisation processing personal data for commercial purposes.

- Register at: `ico.org.uk/registration`
- Fee tier: likely Tier 2 (£60/year for organisations with <250 employees and turnover <£632,000; otherwise Tier 3 at £2,900/year)
- Include in registration: data controller activities (user accounts, audit logs, marketing), data processor activities (customer emissions data, employee commuting data)

### Record of Processing Activities (ROPA)

Required under GDPR Article 30. Maintain internally:

| Activity | Controller/Processor | Purpose | Data categories | Retention | Sub-processors |
|---------|---------------------|---------|----------------|-----------|----------------|
| User accounts | Controller | Service delivery | Name, email, password hash, role | Account lifetime + 90 days | AWS (hosting) |
| Authentication logs | Controller | Security | IP, user agent, timestamp, success/fail | 12 months | AWS |
| Audit logs | Controller (for platform security) / Processor (for customer data) | Compliance, fraud | User ID, entity ID, table, changes | 30d/1yr/7yr per tier | AWS |
| Emissions data | Processor | Customer's GHG reporting | Activity amounts, dates, calculations | Customer's retention period | AWS, Climatiq (EF data only) |
| Employee commuting data | Processor | Customer's Scope 3 Cat 7 | Journey data (may be anonymous) | Customer's retention period | AWS |
| Marketing leads | Controller | Marketing | Email, company, estimated footprint | Until unsubscribe + 6 months | ConvertKit/Loops |
| Payment data | Controller | Billing | Stripe customer ID, invoice refs | 7 years (financial records) | Stripe |

### Data Protection Impact Assessment (DPIA)

Required when processing is likely to result in high risk to individuals. Trigger a DPIA before launching:
- Employee commuting module (if names or identifiable journey data are collected)
- Any feature using AI/ML to infer emissions from indirect data
- Integration with HR systems (potential future feature)

Template: ICO's DPIA template at `ico.org.uk`. Keep on file — not submitted to ICO unless a prior consultation is required.

### Breach notification

Under GDPR Article 33, breaches must be reported to ICO within **72 hours** of becoming aware (if likely to result in risk to individuals).

Process:
1. Sentry alert / security monitoring detects anomaly
2. On-call engineer confirms breach, notifies CTO
3. CTO assesses: personal data involved? Risk to individuals?
4. If yes: notify ICO within 72 hours via `ico.org.uk/make-a-complaint/data-security-incident-report`
5. If high risk to individuals: notify affected users directly (Article 34)
6. Document in internal breach register regardless of severity

Add `BREACH_NOTIFICATION_EMAIL` to `.env` — internal alert recipient for security events from Sentry.

---

## 2. Cyber Essentials (UK)

### What it is

A UK government-backed cybersecurity certification scheme. Two levels:
- **Cyber Essentials** — self-assessed questionnaire, ~£300/year. Covers: firewalls, secure configuration, user access control, malware protection, patch management.
- **Cyber Essentials Plus** — independently verified, ~£1,500–2,500. Includes technical audit.

### Why it matters for SusDevOS

- Required for all UK government contracts (mandatory since 2014)
- Increasingly expected by enterprise procurement teams in the UK
- Shows basic security hygiene to SME customers who can't evaluate security themselves
- Listed on GOV.UK as a trust signal

### Requirements and current compliance status

| Control area | Requirement | SusDevOS implementation |
|-------------|-------------|------------------------|
| Firewalls | Boundary firewall, no unnecessary ports | AWS Security Groups — configure at deployment |
| Secure configuration | Disable unnecessary services, change defaults | Hardening checklist at deployment (see below) |
| User access control | Least privilege, MFA for admin | RBAC already implemented; add MFA for SuperAdmin role |
| Malware protection | Anti-malware on servers | AWS Inspector + GuardDuty |
| Patch management | OS and software patched within 14 days of critical patch | Managed via OS auto-updates + dependabot |

**Gaps to address before certification:**
- MFA for SuperAdmin login — needs implementation (TOTP via `django-otp`)
- Formal patch management policy document
- Formal firewall rule review process

**Target:** Cyber Essentials certification before first enterprise customer. Cyber Essentials Plus for Year 2.

---

## 3. ISO/IEC 27001 — Information Security Management

### What it is

The international standard for an Information Security Management System (ISMS). More comprehensive than Cyber Essentials — covers risk management, security policies, incident response, business continuity.

### Roadmap

ISO 27001 certification typically takes 6–12 months and costs £15,000–40,000 (consultant + audit fees).

**Phase 1 (pre-certification, now):** Implement controls already in the system design:
- Access control policy — document the RBAC model
- Encryption policy — document AES-256 at rest, TLS 1.3 in transit
- Incident response procedure — document the breach notification process above
- Asset register — list all systems, data flows, third-party processors
- Risk register — identify and score risks (e.g. Climatiq API goes down, Stripe outage, data breach)

**Phase 2 (Year 1):** Formal ISMS scope definition + Statement of Applicability. Internal audit. Gap analysis against ISO 27001:2022 Annex A controls.

**Phase 3 (Year 2):** Stage 1 audit (documentation review) + Stage 2 audit (implementation verification). Certification issued. Annual surveillance audits thereafter.

**Certification body options (UK):** BSI, LRQA, Alcumus. Budget ~£8,000–15,000 for initial certification for a small SaaS.

### Controls most relevant to SusDevOS

| ISO 27001 control | Implementation |
|-----------------|---------------|
| A.5.1 Policies | Security policy document — publish at /security |
| A.8.2 Privileged access | SuperAdmin accounts tracked in AuditLog; MFA required |
| A.8.3 Information access restriction | RBAC + FeatureGateMixin |
| A.8.7 Protection against malware | AWS GuardDuty |
| A.8.12 Data leakage prevention | TenantQueryMiddleware enforces entity isolation |
| A.8.15 Logging | AuditLog + Sentry + CloudWatch |
| A.8.24 Use of cryptography | AES-256 at rest, TLS 1.3 in transit, Argon2id passwords |
| A.5.29 Information security during disruption | RDS automated backups, multi-AZ deployment |
| A.5.34 Privacy and PII | GDPR controls above |

---

## 4. SOC 2 Type II

### What it is

An American auditing standard (AICPA) covering five Trust Service Criteria: Security, Availability, Processing Integrity, Confidentiality, Privacy. Type II means controls were tested over a period (typically 6–12 months), not just described.

### Why it matters

SOC 2 Type II is the enterprise procurement standard in the US and increasingly globally. Without it, most US enterprise customers cannot onboard SusDevOS — their security teams require it.

### Timeline and cost

- **Readiness assessment:** ~£5,000 (consultant reviews existing controls)
- **Audit period:** 6 months minimum (12 months preferred for Type II)
- **Audit cost:** £20,000–50,000 depending on auditor and scope
- **Realistic target:** Complete Type II audit in Year 2 if US enterprise is a priority market

### Relevant controls already implemented

The SusDevOS architecture covers most SOC 2 Security criteria already:
- Logical access controls (RBAC and JWT; customer API keys are deferred during PMF)
- Encryption (AES-256 at rest, TLS 1.3)
- Monitoring and logging (AuditLog, Sentry, CloudWatch)
- Incident response process (breach notification procedure)
- Change management (migrations, Git history)
- Vendor management (documented sub-processor list in ROPA)

**Gaps:** Formal penetration testing, business continuity plan, disaster recovery testing documentation, formal employee security training programme.

### Tooling

Consider **Drata**, **Vanta**, or **Secureframe** for continuous SOC 2 compliance monitoring. These tools auto-collect evidence from AWS, GitHub, and HR systems. ~$500–1,000/month but saves significant manual audit prep time.

---

## 5. CCPA / CPRA (California)

### Applicability

The California Consumer Privacy Act (CCPA), enhanced by CPRA, applies if SusDevOS:
- Does business in California, AND
- Has annual gross revenue > $25M, OR processes data of ≥ 100,000 California consumers/households, OR sells personal data

Likely not immediately applicable at launch, but will apply once US customers are onboarded.

### Key requirements

- Privacy policy must disclose: what personal data is collected, why, with whom it's shared, and how long it's kept
- California residents have rights similar to GDPR: access, deletion, correction, portability, opt-out of sale
- "Do Not Sell or Share My Personal Information" link required in footer if selling/sharing data (SusDevOS does not sell data — link can state "We do not sell your personal information")
- Data processing records required

**Implementation:** The GDPR-compliant privacy policy covers most CCPA requirements. Add a California-specific section to `/legal/privacy` and the "Do Not Sell" statement to the footer.

---

## 6. CSRD (Corporate Sustainability Reporting Directive)

### What it is

EU law (in force from 2024/2025) requiring large and listed companies to report sustainability information under the European Sustainability Reporting Standards (ESRS). Replaces NFRD.

### Relevance to SusDevOS

SusDevOS is not required to report under CSRD (not a large company). But **SusDevOS's customers** increasingly are — and CSRD is a major driver for demand for GHG reporting software.

### What CSRD means for the product

ESRS E1 (Climate change) requires disclosure of:
- Scope 1, 2, and 3 GHG emissions — already covered
- GHG intensity metrics — add `IntensityMetric` reporting to the GHGInventories report
- Transition plans and targets — Targets module already covers this
- Carbon credits and removals — EmissionsOffsets module covers this
- TCFD-aligned disclosures — already in spec

ESRS E4 (Biodiversity and ecosystems) requires:
- Identification of material sites for biodiversity
- Targets related to biodiversity
- Species and ecosystem impact assessment

SusDevOS's ecosystem module covers significant ground on E4. Adding explicit ESRS E4 report output is a meaningful differentiator — very few tools support it alongside GHG.

**Action:** Add `CSRD/ESRS-ready` to the Standards & Compliance marketing page. Add an ESRS E1 + E4 export format to the reports module (future milestone).

---

## 7. Application-Layer Changes Required

### MFA for SuperAdmin (Cyber Essentials requirement)

Add `django-otp` + `django-two-factor-auth`. Required only for users with `SuperAdmin` role.

```python
# New field on Users model (migration 0029)
('TOTPDeviceVerified', models.BooleanField(default=False,
    help_text="True if user has enrolled a TOTP device. Required for SuperAdmin role."))
```

Middleware check: if `request.user.Role.RoleName == 'SuperAdmin'` and not `TOTPDeviceVerified`, redirect to `/app/mfa/setup/` before any API request is processed.

### Data export endpoint (GDPR right of access)

```
GET /api/users/me/data-export/
```

Returns: user record, last 12 months of audit log entries for this user, and notification history. Async: triggers Celery task, emails ZIP download link within 1 hour. Download link expires after 24 hours.

### Account anonymisation (GDPR right to erasure)

```
DELETE /api/users/me/
```

Does not hard-delete. Sets `DeletedAt`, anonymises PII fields. `ChangedBy` FK on AuditLog set to NULL, `ChangedByUsername` snapshot retained (necessary for inventory integrity — verifiers need to know who submitted what).

### Personal data minimisation in Sentry

Configure Sentry's `before_send` hook to strip email addresses, names, and IP addresses from error reports before they leave the server:

```python
# config/sentry.py
def before_send(event, hint):
    if "user" in event:
        event["user"].pop("email", None)
        event["user"].pop("ip_address", None)
    return event
```

### Audit log retention enforcement

The `RetentionTier` field on `AuditLog` maps to:
- Tier 1 (30 days): Free + Starter plans
- Tier 2 (1 year): Professional + Agency plans
- Tier 3 (7 years): Enterprise plans (regulatory requirement for financial records)

Celery beat task `tasks.auth.purge_expired_audit_logs` (nightly):

```python
@shared_task(name="tasks.auth.purge_expired_audit_logs")
def purge_expired_audit_logs():
    now = timezone.now()
    AuditLog.objects.filter(RetentionTier=1, CreatedAt__lt=now - timedelta(days=30)).delete()
    AuditLog.objects.filter(RetentionTier=2, CreatedAt__lt=now - timedelta(days=365)).delete()
    # Tier 3: never auto-deleted — manual process with legal sign-off
```

### Sub-processor notification

When SusDevOS adds a new third-party sub-processor (e.g. a new integration), GDPR requires notifying customers and giving them a right to object. Implement:
- Public sub-processor list at `/legal/sub-processors` — maintained as a static page
- Email notification to all `Admin` and `SuperAdmin` users when the list changes (30 days notice)

---

## 8. Environment Variables Added

```bash
# Data protection
BREACH_NOTIFICATION_EMAIL=security@yourdomain.com
DPO_EMAIL=dpo@yourdomain.com
ICO_REGISTRATION_NUMBER=                   # set after ICO registration

# Sentry (PII scrubbing enabled in before_send hook)
SENTRY_DSN=
SENTRY_ENVIRONMENT=production

# MFA
OTP_TOTP_ISSUER=SusDevOS                   # shown in authenticator app
```

---

## 9. Documentation Required (maintain in /docs/internal)

- Privacy Policy (customer-facing, at /legal/privacy)
- Data Processing Agreement template (/legal/dpa)
- Sub-processor list (/legal/sub-processors)
- Internal ROPA (Record of Processing Activities)
- Security Policy (internal; summary at /security)
- Incident Response Procedure
- Data Retention Schedule
- DPIA template (completed before high-risk features launch)
- Breach Register (internal, never published)
