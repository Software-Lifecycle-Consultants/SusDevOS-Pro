# SusDevOS Documentation

## User Guides

Role-specific guides covering the core workflows for each user type.

| Guide | For | Key topics |
|-------|-----|-----------|
| [Admin Guide](user-guide-admin.md) | Organisation admins and account holders | Entity setup, user management, inventory verification, audit log, billing |
| [Sustainability Manager Guide](user-guide-sustainability-manager.md) | Sustainability managers and ESG leads | GHG inventory, Scope 1/2/3, reduction targets, offsets, reports |
| [ESG Consultant Guide](user-guide-esg-consultant.md) | Sustainability consultancies (Agency plan) | Multi-client management, verification workflow, white-label reports, client portal |
| [Project Manager Guide](user-guide-project-manager.md) | Development and land project managers | Projects, land parcels, ecosystem surveys, tree removals, restorations, TNFD |

## Technical Reference

| Document | Covers |
|----------|--------|
| [App Structure](../spec/app_structure.md) | 12 Django apps, model list, migration chain |
| [Endpoint Catalog](../spec/endpoint_catalog.md) | ~100 REST endpoints, request/response shapes |
| [Privilege System](../spec/privilege_system_resolved.md) | RBAC: Modules → Interfaces → RolePrivileges |
| [GHG Calculation Spec](../spec/ghg_calculation_spec.md) | GHG formulas, unit conversion, dual Scope 2 |
| [API Integrations](../spec/api_integrations.md) | Climatiq, Companies House, Verra, ECB FX, GBIF |
| [Celery Tasks](../spec/celery_tasks.md) | Background tasks, schedules, retry policies |
| [Pricing](../spec/pricing.md) | Plan tiers, feature gate matrix |
| [Compliance](../spec/compliance.md) | GDPR, Cyber Essentials, ISO 27001 roadmap |

## Deployment

| Document | Covers |
|----------|--------|
| [Deployment Guide](deployment.md) | Hetzner VPS setup, Docker Compose prod config, SSL, GitHub Actions deploy, backups, monitoring |

## Active Audits

| Document | Covers |
|----------|--------|
| [Core Feature Integrity Audit](audits/core-feature-integrity-audit.md) | End-to-end user flows, field lineage, confirmed defects, execution order, and closure evidence |

## Architecture Decisions

| Document | Status | Covers |
|----------|--------|--------|
| [ADR 0001 — Project-centric workspace](decisions/0001-project-centric-workspace.md) | Proposed | Project as the operational workspace while entity, inventory, and parcel remain authoritative boundaries |

## Proposed Design Gates

These documents describe target behavior and are **not** claims about the current application.
They must be reviewed together before implementation starts.

| Document | Covers |
|----------|--------|
| [Project workspace UML](diagrams/proposed/01-project-centric-workspace-uml.md) | Existing canonical relationships, read models, invariants, and deferred schema concepts |
| [Project workspace BPMN](diagrams/proposed/02-project-centric-workspace-bpmn.md) | Project-, inventory-, and parcel-originated flows plus reporting and lifecycle exceptions |
| [Project workspace user stories](stories/08-project-workspace.md) | Observable acceptance criteria for the migration-free first slice |

## Developer Setup

See the main [README](../README.md) for Docker-based local setup, seed commands, and running tests.
