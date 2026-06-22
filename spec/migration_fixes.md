# SusDevOS — Migration Fixes Reference

This document records every fix applied to the original Notion migration files.
Reference this when reviewing the original files against the corrected versions.

---

## 1. Missing migrations (added)

| File | Content |
|------|---------|
| `0010_gwp_datasets.py` | `GwpDatasets`, `GwpValues` tables + seed data (IPCC AR6 GWP100) |
| `0011_emissions.py` | `EmissionsData`, `EmissionsDetails`, `EmissionsOffsets` — the core domain model |
| `0012_shared_modules_fixed.py` | Shared tables (Locations, Contacts, Documents, Images, Tags, EntityApiKeys) with all FK fixes applied |
| `0013_auth_tokens.py` | `PasswordResetTokens`, `RevokedTokens` |
| `0014_notifications.py` | `Notifications` |
| `0015_blogs.py` | `Blogs` |
| `0016_audit_log_revised.py` | `AuditLog` — revised schema replacing the original `AuditLogs` |
| `0017_report_jobs.py` | `ReportJobs` — async report generation tracking |
| `0018_user_privilege_overrides.py` | `UserPrivilegeOverrides` — per-user privilege grant/revoke |

---

## 2. FK inconsistencies fixed

The following fields in the original migrations used bare `IntegerField` where they should be `ForeignKey`. This meant Django would not enforce referential integrity.

| Table | Field | Original | Fixed |
|-------|-------|----------|-------|
| `DevelopmentProjectLandParcels` | `LandParcelId` | `IntegerField()` | `ForeignKey('land.LandParcels')` |
| `DevelopmentProjectContacts` | `ContactId` | `IntegerField()` | `ForeignKey('shared.Contacts')` |
| `DevelopmentProjectDocuments` | `DocumentId` | `IntegerField()` | `ForeignKey('shared.Documents')` |
| `DevelopmentProjectImages` | `ImageId` | `IntegerField()` | `ForeignKey('shared.Images')` |
| `DevelopmentProjectTags` | `TagId` | `IntegerField()` | `ForeignKey('shared.Tags')` |
| `LandParcelContacts` | `ContactId` | `IntegerField()` | `ForeignKey('shared.Contacts')` |
| `LandParcelDocuments` | `DocumentId` | `IntegerField()` | `ForeignKey('shared.Documents')` |
| `LandParcelImages` | `ImageId` | `IntegerField()` | `ForeignKey('shared.Images')` |
| `LandParcelLocations` | `LocationId` | `IntegerField()` | `ForeignKey('shared.Locations')` |
| `TreeRemovalContacts` | `ContactId` | `IntegerField()` | `ForeignKey('shared.Contacts')` |
| `TreeRemovalDocuments` | `DocumentId` | `IntegerField()` | `ForeignKey('shared.Documents')` |
| `TreeRemovalLandParcels` | `LandParcelId` | `IntegerField()` | `ForeignKey('land.LandParcels')` |
| `TreeRemovalRemovedSpecies` | `SpeciesId` | `IntegerField()` | `ForeignKey('ecosystem.Species')` |
| `TreeRemovalAffectedSpecies` | `SpeciesId` | `IntegerField()` | `ForeignKey('ecosystem.Species')` |
| `RestorationLandParcels` | `LandParcelId` | `IntegerField()` | `ForeignKey('land.LandParcels')` |
| `RestorationSpecies` | `SpeciesId` | `IntegerField()` | `ForeignKey('ecosystem.Species')` |
| `RestorationDevelopmentProjects` | `DevelopmentProjectId` | `IntegerField()` | `ForeignKey('projects.DevelopmentProjects')` |
| `SpeciesLandParcels` | `LandParcelId` | `IntegerField()` | Kept as IntegerField intentionally — circular dependency between `ecosystem` and `land` apps. Documented in app_structure.md. |

---

## 3. JSONField → junction table (Documents and Images tags)

**Original:** `Documents.TagIDs = JSONField(default=list)` and `Images.TagIDs = JSONField(default=list)`

**Problem:** Inconsistent with every other M2M in the schema which uses junction tables. Tag deletion would require a fragile background job scanning JSON fields.

**Fix:** Removed `TagIDs` JSONField from both models. Added proper junction tables:
- `DocumentTags (id, DocumentId FK, TagId FK)`
- `ImageTags (id, ImageId FK, TagId FK)`

---

## 4. Contacts.ModuleID — free-text CharField fixed

**Original:** `Contacts.ModuleID = CharField(max_length=20)` with no constraint on valid values.

**Problem:** Any string could be inserted; no validation at DB or application layer. Also renamed confusingly (ModuleID implies an integer FK).

**Fix:** Renamed to `ModuleKey`, type kept as `CharField` but now uses `choices=MODULE_KEY_CHOICES` — an explicit enum of valid module keys matching the modules fixture. Invalid values raise a validation error.

Same fix applied to `Documents.ModuleKey`.

---

## 5. RelatedEntities / RelatedProjects on_delete behaviour

**Original:** Both junction FKs used `on_delete=models.SET_NULL` with `null=True, blank=True`.

**Problem:** If either parent is deleted, the junction row becomes a null-null record — meaningless data that accumulates silently.

**Fix:** Changed to `on_delete=models.CASCADE` on both FKs. If either parent entity/project is soft-deleted (Status=4), the junction record is also removed. Note: the original spec soft-deletes by setting `Status=4`, not by deleting the row, so CASCADE is only triggered on hard deletes (which the spec says should not happen). This is a safety net for data integrity.

---

## 6. AuditLog schema conflict

**Original Notion spec:** Defined `AuditLogs` with `UserId`, `UserName`, `Action`, `TargetTable`, `TargetRecordId`, `Description`, `Status`, `CreatedAt`, `UpdatedAt` — no tenant FK, no change snapshots, no security metadata.

**Gaps & Resolutions doc (section 7.3):** Defined a completely different schema with `OldValues`, `NewValues`, `IpAddress`, `UserAgent`, `RetentionTier`.

**Fix:** The revised schema from the Gaps doc is authoritative. `0016_audit_log_revised.py` implements it with additional improvements:
- `BIGINT` primary key for high-volume write throughput
- `EntityId` FK for tenant-scoped Admin filtering
- `RetentionTier` field to drive the Celery Beat cleanup task
- Denormalised `ChangedByUsername` snapshot in case user is soft-deleted later

The original `AuditLogs` migration should not be applied. Use `0016_audit_log_revised.py` exclusively.

---

## 7. Privilege system — two conflicting documents

**Original Enhanced Privilege System Design doc:** `Features` table with `PrivilegeID`-centric model and `x-*` wildcard notation.

**Original migration files:** `Modules → Interfaces → RolePrivileges` with `PermissionType` integer.

**Fix:** The Modules/Interfaces/RolePrivileges pattern is used. The Features/PrivilegeID design is retired. See `spec/privilege_system_resolved.md` for the complete resolved design.

`0018_user_privilege_overrides.py` adds the missing `UserPrivilegeOverrides` table which enables per-user grant/revoke exceptions without the complexity of the original wildcard notation.

---

## 8. `your_app` placeholder in all original migrations

**Original:** All migrations reference `('your_app', '...')` as the app label.

**Fix:** All new migrations use proper app labels matching the app structure in `spec/app_structure.md`. The original Notion migrations need to be updated with the correct app labels when the Django project is scaffolded.
