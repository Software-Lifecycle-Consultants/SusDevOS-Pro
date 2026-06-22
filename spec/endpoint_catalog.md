# SusDevOS — API Endpoint Catalog

Base URL: `/api/v1/`  
Public base URL: `/api/public/`  
All authenticated endpoints require `Authorization: Bearer <access_token>`.  
All responses follow the standard envelope: `{ success, data, meta, errors }`.  
All list endpoints support: `?page=1&pageSize=20&sortBy=<field>&sortDir=asc|desc&search=<query>`

### Permission Roles
- **SA** = SuperAdmin
- **A** = Admin (entity-scoped)
- **M** = Manager (entity-scoped)
- **S** = Staff (entity-scoped)

---

## Auth

| Method | Path | Permissions | Notes |
|--------|------|-------------|-------|
| POST | `/auth/login` | Public | Body: `{ username, password }` → `{ access_token, user }` + HttpOnly refresh cookie |
| POST | `/auth/logout` | Any | Invalidates refresh token server-side |
| POST | `/auth/refresh` | Public | Uses HttpOnly cookie → new access token |
| POST | `/auth/forgot-password` | Public | Body: `{ email }` → sends reset email |
| POST | `/auth/reset-password` | Public | Body: `{ token, new_password }` |
| POST | `/auth/onboard` | Public | Body: `{ token, new_password }` — first login for newly created users |
| GET | `/auth/me` | Any | Returns authenticated user profile + effective privileges |

---

## Entities

| Method | Path | Permissions | Notes |
|--------|------|-------------|-------|
| GET | `/entities/` | SA, A | SA sees all; A sees own entity + related (branches) |
| POST | `/entities/` | SA | Create entity + assign initial Admin |
| GET | `/entities/{id}/` | SA, A | |
| PATCH | `/entities/{id}/` | SA, A | |
| DELETE | `/entities/{id}/` | SA | Soft delete (Status=4) |
| GET | `/entities/{id}/locations/` | SA, A, M | |
| POST | `/entities/{id}/locations/` | SA, A | Link existing location |
| DELETE | `/entities/{id}/locations/{locationId}/` | SA, A | Unlink |
| GET | `/entities/{id}/contacts/` | SA, A, M | |
| POST | `/entities/{id}/contacts/` | SA, A, M | |
| GET | `/entities/{id}/documents/` | SA, A, M | |
| POST | `/entities/{id}/documents/` | SA, A, M | |
| GET | `/entities/{id}/api-keys/` | SA, A | |
| POST | `/entities/{id}/api-keys/` | SA, A | Generate new key |
| DELETE | `/entities/{id}/api-keys/{keyId}/` | SA, A | Revoke key |
| GET | `/entities/{id}/settings/` | SA, A | Entity-level settings (ShareEmissions etc.) |
| PATCH | `/entities/{id}/settings/` | SA, A | |

---

## Users

| Method | Path | Permissions | Notes |
|--------|------|-------------|-------|
| GET | `/users/` | SA, A, M | SA: all; A: entity + related entities; M: own entity only |
| POST | `/users/` | SA, A, M | A can create Admin/Manager/Staff; M can create Staff only |
| GET | `/users/{id}/` | SA, A, M | |
| PATCH | `/users/{id}/` | SA, A | |
| DELETE | `/users/{id}/` | SA, A | Soft delete |
| GET | `/users/me/` | Any | Own profile |
| PATCH | `/users/me/` | Any | Update own profile (bio, designation, profile picture) |
| PATCH | `/users/me/password/` | Any | Change own password |
| GET | `/users/{id}/privileges/` | SA, A | Returns effective privilege set (role-based + overrides) |
| POST | `/users/{id}/privileges/override/` | SA, A | Add grant/revoke override for a specific interface |
| DELETE | `/users/{id}/privileges/override/{overrideId}/` | SA, A | Remove override |

---

## Roles & Modules

| Method | Path | Permissions | Notes |
|--------|------|-------------|-------|
| GET | `/roles/` | SA, A | List all defined roles |
| GET | `/roles/{id}/` | SA, A | |
| GET | `/roles/{id}/privileges/` | SA, A | All RolePrivileges for this role |
| GET | `/modules/` | SA, A | List all modules |
| GET | `/modules/{id}/interfaces/` | SA, A | List all interfaces within a module |

Note: Roles and modules are seeded — not created at runtime in v1.0.

---

## Projects

| Method | Path | Permissions | Notes |
|--------|------|-------------|-------|
| GET | `/projects/` | SA, A, M, S | Tenant-scoped |
| POST | `/projects/` | SA, A, M | |
| GET | `/projects/{id}/` | SA, A, M, S | |
| PATCH | `/projects/{id}/` | SA, A, M | |
| DELETE | `/projects/{id}/` | SA, A | Soft delete |
| GET | `/projects/{id}/phases/` | SA, A, M, S | |
| POST | `/projects/{id}/phases/` | SA, A, M | |
| GET | `/projects/{id}/phases/{phaseId}/` | SA, A, M, S | |
| PATCH | `/projects/{id}/phases/{phaseId}/` | SA, A, M | |
| DELETE | `/projects/{id}/phases/{phaseId}/` | SA, A | |
| GET | `/projects/{id}/emissions/` | SA, A, M, S | All emissions records for this project |
| GET | `/projects/{id}/emissions/summary/` | SA, A, M | Scope 1/2/3 totals in tCO2e |
| GET | `/projects/{id}/land-parcels/` | SA, A, M, S | |
| POST | `/projects/{id}/land-parcels/` | SA, A, M | Link parcel to project |
| DELETE | `/projects/{id}/land-parcels/{parcelId}/` | SA, A, M | Unlink |
| GET | `/projects/{id}/partners/` | SA, A, M, S | |
| POST | `/projects/{id}/partners/` | SA, A, M | |
| DELETE | `/projects/{id}/partners/{partnerId}/` | SA, A, M | |
| GET | `/projects/{id}/documents/` | SA, A, M, S | |
| POST | `/projects/{id}/documents/` | SA, A, M | |
| GET | `/projects/{id}/images/` | SA, A, M, S | |
| POST | `/projects/{id}/images/` | SA, A, M | |

---

## Land Parcels

| Method | Path | Permissions | Notes |
|--------|------|-------------|-------|
| GET | `/land-parcels/` | SA, A, M, S | |
| POST | `/land-parcels/` | SA, A, M | GeoData must be valid GeoJSON Polygon/MultiPolygon in WGS84 |
| GET | `/land-parcels/{id}/` | SA, A, M, S | |
| PATCH | `/land-parcels/{id}/` | SA, A, M | |
| DELETE | `/land-parcels/{id}/` | SA, A | Soft delete |
| GET | `/land-parcels/{id}/overlap-check/` | SA, A, M | Returns overlapping parcel titles via PostGIS ST_Intersects |
| GET | `/land-parcels/{id}/ecosystems/` | SA, A, M, S | |
| POST | `/land-parcels/{id}/ecosystems/` | SA, A, M | Link ecosystem |
| DELETE | `/land-parcels/{id}/ecosystems/{ecosystemId}/` | SA, A, M | |
| GET | `/land-parcels/{id}/species/` | SA, A, M, S | All species for this parcel |
| GET | `/land-parcels/{id}/documents/` | SA, A, M, S | |
| POST | `/land-parcels/{id}/documents/` | SA, A, M | |

---

## Ecosystems

| Method | Path | Permissions | Notes |
|--------|------|-------------|-------|
| GET | `/ecosystems/` | SA, A, M, S | |
| POST | `/ecosystems/` | SA, A, M | |
| GET | `/ecosystems/{id}/` | SA, A, M, S | |
| PATCH | `/ecosystems/{id}/` | SA, A, M | |
| DELETE | `/ecosystems/{id}/` | SA, A | Soft delete |

---

## Species

| Method | Path | Permissions | Notes |
|--------|------|-------------|-------|
| GET | `/species/` | SA, A, M, S | |
| POST | `/species/` | SA, A, M | |
| GET | `/species/{id}/` | SA, A, M, S | |
| PATCH | `/species/{id}/` | SA, A, M | |
| DELETE | `/species/{id}/` | SA, A | Soft delete |
| GET | `/species/{id}/land-parcels/` | SA, A, M, S | Parcels where this species is recorded |

---

## Tree Removals

| Method | Path | Permissions | Notes |
|--------|------|-------------|-------|
| GET | `/tree-removals/` | SA, A, M, S | |
| POST | `/tree-removals/` | SA, A, M | |
| GET | `/tree-removals/{id}/` | SA, A, M, S | |
| PATCH | `/tree-removals/{id}/` | SA, A, M | |
| DELETE | `/tree-removals/{id}/` | SA, A | Soft delete |
| GET | `/tree-removals/{id}/removed-species/` | SA, A, M, S | |
| POST | `/tree-removals/{id}/removed-species/` | SA, A, M | |
| PATCH | `/tree-removals/{id}/removed-species/{recordId}/` | SA, A, M | |
| DELETE | `/tree-removals/{id}/removed-species/{recordId}/` | SA, A, M | |
| GET | `/tree-removals/{id}/affected-species/` | SA, A, M, S | |
| POST | `/tree-removals/{id}/affected-species/` | SA, A, M | |
| PATCH | `/tree-removals/{id}/affected-species/{recordId}/` | SA, A, M | |
| DELETE | `/tree-removals/{id}/affected-species/{recordId}/` | SA, A, M | |

---

## Restorations

| Method | Path | Permissions | Notes |
|--------|------|-------------|-------|
| GET | `/restorations/` | SA, A, M, S | |
| POST | `/restorations/` | SA, A, M | |
| GET | `/restorations/{id}/` | SA, A, M, S | |
| PATCH | `/restorations/{id}/` | SA, A, M | |
| DELETE | `/restorations/{id}/` | SA, A | Soft delete |
| GET | `/restorations/{id}/species/` | SA, A, M, S | |
| POST | `/restorations/{id}/species/` | SA, A, M | |
| PATCH | `/restorations/{id}/species/{recordId}/` | SA, A, M | |
| DELETE | `/restorations/{id}/species/{recordId}/` | SA, A, M | |

---

## Emissions

| Method | Path | Permissions | Notes |
|--------|------|-------------|-------|
| GET | `/emissions/` | SA, A, M, S | Filter by `?projectId=`, `?scope=`, `?phaseId=`, `?verificationStatus=` |
| POST | `/emissions/` | SA, A, M | Frontend sends raw quantities; server computes EmissionsAmount |
| GET | `/emissions/{id}/` | SA, A, M, S | |
| PATCH | `/emissions/{id}/` | SA, A, M | Blocked if VerificationStatus=Verified |
| DELETE | `/emissions/{id}/` | SA, A | Blocked if VerificationStatus=Verified |
| POST | `/emissions/{id}/verify/` | SA, A | Sets VerificationStatus=Verified; record becomes immutable |
| POST | `/emissions/{id}/unlock/` | SA | SuperAdmin only; creates mandatory AuditLog entry with reason |
| GET | `/emissions/{id}/details/` | SA, A, M, S | Line items |
| POST | `/emissions/{id}/details/` | SA, A, M | |
| PATCH | `/emissions/{id}/details/{detailId}/` | SA, A, M | |
| DELETE | `/emissions/{id}/details/{detailId}/` | SA, A, M | |
| GET | `/emissions/{id}/offsets/` | SA, A, M, S | Carbon offset records |
| POST | `/emissions/{id}/offsets/` | SA, A, M | |
| PATCH | `/emissions/{id}/offsets/{offsetId}/` | SA, A, M | |
| DELETE | `/emissions/{id}/offsets/{offsetId}/` | SA, A, M | |
| POST | `/emissions/import/` | SA, A, M | CSV bulk import; returns job ID for async processing |

---

## GWP Datasets

| Method | Path | Permissions | Notes |
|--------|------|-------------|-------|
| GET | `/gwp-datasets/` | Any | List all datasets; IsDefault flag shown |
| GET | `/gwp-datasets/{id}/` | Any | |
| GET | `/gwp-datasets/{id}/values/` | Any | All gas GWP factors for this dataset |
| POST | `/gwp-datasets/` | SA | Add new GWP dataset |
| POST | `/gwp-datasets/{id}/recalculate/` | SA, A | Trigger recalculation job for all EmissionsData using this dataset |

---

## Reports

| Method | Path | Permissions | Notes |
|--------|------|-------------|-------|
| GET | `/reports/` | SA, A, M | List report jobs for tenant |
| GET | `/reports/{id}/` | SA, A, M | Check job status |
| GET | `/reports/{id}/download/` | SA, A, M | Returns pre-signed S3 URL (expires 24h) |
| POST | `/reports/emissions-summary/` | SA, A, M | Body: `{ projectId, format: pdf|json, reportingPeriodFrom, reportingPeriodTo }` |
| POST | `/reports/ghg-inventory/` | SA, A, M | Body: `{ entityId, format: pdf|csv, baselineYear, reportingPeriodFrom, reportingPeriodTo }` |
| POST | `/reports/phase-progress/` | SA, A, M | Body: `{ projectId, phaseId?, format: pdf }` |
| POST | `/reports/tree-log/` | SA, A, M | Body: `{ entityId, format: pdf|csv, from, to }` |

---

## Shared Resources

### Locations (Global — not entity-scoped)
| Method | Path | Permissions | Notes |
|--------|------|-------------|-------|
| GET | `/locations/` | Any | Search with `?city=&country=` |
| POST | `/locations/` | Any | City + Country uniqueness warned but not blocked |
| GET | `/locations/{id}/` | Any | |
| PATCH | `/locations/{id}/` | SA, A | Edit (never deleted) |

### Contacts (Entity-scoped)
| Method | Path | Permissions | Notes |
|--------|------|-------------|-------|
| GET | `/contacts/` | SA, A, M, S | Tenant-scoped |
| POST | `/contacts/` | SA, A, M | |
| GET | `/contacts/{id}/` | SA, A, M, S | |
| PATCH | `/contacts/{id}/` | SA, A, M | |
| DELETE | `/contacts/{id}/` | SA, A | Soft delete; renders as [Deleted] in parent records |

### Documents & Images
| Method | Path | Permissions | Notes |
|--------|------|-------------|-------|
| GET | `/documents/` | SA, A, M, S | |
| POST | `/documents/` | SA, A, M | After uploading file via pre-signed URL |
| PATCH | `/documents/{id}/` | SA, A, M | |
| DELETE | `/documents/{id}/` | SA, A | Soft delete; S3 purge after 30 days |
| GET | `/images/` | SA, A, M, S | |
| POST | `/images/` | SA, A, M | |
| PATCH | `/images/{id}/` | SA, A, M | |
| DELETE | `/images/{id}/` | SA, A | |

### Tags (Entity-scoped)
| Method | Path | Permissions | Notes |
|--------|------|-------------|-------|
| GET | `/tags/` | SA, A, M, S | |
| POST | `/tags/` | SA, A, M | Case-insensitive dedup on save |
| DELETE | `/tags/{id}/` | SA, A | Triggers background job to scrub junction tables |

### File Upload
| Method | Path | Permissions | Notes |
|--------|------|-------------|-------|
| POST | `/files/upload-url/` | SA, A, M | Body: `{ fileName, mimeType, module, recordId }` → returns `{ uploadUrl, fileKey }` |

---

## Notifications

| Method | Path | Permissions | Notes |
|--------|------|-------------|-------|
| GET | `/notifications/` | Any | Tenant + user scoped; supports `?isRead=false` |
| GET | `/notifications/unread-count/` | Any | Returns `{ count: N }` — used by polling (every 60s) |
| PATCH | `/notifications/{id}/read/` | Any | Mark single as read |
| POST | `/notifications/mark-all-read/` | Any | |

---

## Blog

### Authenticated (CMS)
| Method | Path | Permissions | Notes |
|--------|------|-------------|-------|
| GET | `/blog/` | SA, A | Lists all posts including drafts |
| POST | `/blog/` | SA, A | Status defaults to Draft |
| GET | `/blog/{id}/` | SA, A | |
| PATCH | `/blog/{id}/` | SA, A | |
| POST | `/blog/{id}/publish/` | SA, A | Transitions Draft → Published; irreversible |
| POST | `/blog/{id}/archive/` | SA, A | Transitions Published → Archived |

### Public (no authentication)
| Method | Path | Permissions | Notes |
|--------|------|-------------|-------|
| GET | `/api/public/blog/` | Public | Published posts only; supports `?page=&pageSize=` |
| GET | `/api/public/blog/{slug}/` | Public | Single published post by slug |

---

## Audit Logs

| Method | Path | Permissions | Notes |
|--------|------|-------------|-------|
| GET | `/audit-logs/` | SA, A | Filter by `?tableName=&action=&userId=&from=&to=`; A sees own entity only |
| GET | `/audit-logs/{id}/` | SA, A | |

---

## Standard Request/Response Shapes

### Standard List Response
```json
{
  "success": true,
  "data": [...],
  "meta": {
    "page": 1,
    "pageSize": 20,
    "total": 154,
    "totalPages": 8
  },
  "errors": null
}
```

### Standard Error Response
```json
{
  "success": false,
  "data": null,
  "errors": [
    { "field": "email", "code": "DUPLICATE", "message": "Email already in use." }
  ]
}
```

### Error Codes (used in `errors[].code`)
| Code | Meaning |
|------|---------|
| `REQUIRED` | Field is mandatory |
| `DUPLICATE` | Unique constraint violation |
| `INVALID_FORMAT` | Format validation failed (email, UUID, date etc.) |
| `INVALID_GEOMETRY` | GeoJSON validation failed |
| `MAX_LENGTH` | Exceeds character limit |
| `IMMUTABLE` | Record is verified and cannot be edited |
| `FORBIDDEN` | Authenticated but not authorised |
| `NOT_FOUND` | Resource does not exist |
| `RATE_LIMITED` | Too many requests |
| `CALCULATION_ERROR` | Emissions formula error (bad emission factor etc.) |
