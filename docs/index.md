# SusDevOS Documentation

## User Guides

Role-specific guides covering the core workflows for each user type.

| Guide | For | Key topics |
|-------|-----|-----------|
| [Admin Guide](user-guide-admin.md) | Organisation admins and account holders | Entity setup, user management, inventory verification, audit log, billing |
| [Sustainability Manager Guide](user-guide-sustainability-manager.md) | Sustainability managers and ESG leads | GHG inventory, Scope 1/2/3, SBTi targets, offsets, CDP export, reports |
| [ESG Consultant Guide](user-guide-esg-consultant.md) | Sustainability consultancies (Agency plan) | Multi-client management, verification workflow, white-label reports, client portal |
| [Project Manager Guide](user-guide-project-manager.md) | Development and land project managers | Projects, land parcels, ecosystem surveys, tree removals, restorations, TNFD |

## Technical Reference

| Document | Covers |
|----------|--------|
| [App Structure](../spec/app_structure.md) | 12 Django apps, model list, migration chain |
| [Endpoint Catalog](../spec/endpoint_catalog.md) | ~100 REST endpoints, request/response shapes |
| [Privilege System](../spec/privilege_system_resolved.md) | RBAC: Modules → Interfaces → RolePrivileges |
| [GHG Calculation Spec](../spec/ghg_calculation_spec.md) | GHG formulas, unit conversion, dual Scope 2 |
| [API Integrations](../spec/api_integrations.md) | Climatiq, Companies House, Verra, ECB FX, SBTi, GBIF |
| [Celery Tasks](../spec/celery_tasks.md) | Background tasks, schedules, retry policies |
| [Pricing](../spec/pricing.md) | Plan tiers, feature gate matrix |
| [Compliance](../spec/compliance.md) | GDPR, Cyber Essentials, ISO 27001 roadmap |

## Developer Setup

See the main [README](../README.md) for Docker-based local setup, seed commands, and running tests.
