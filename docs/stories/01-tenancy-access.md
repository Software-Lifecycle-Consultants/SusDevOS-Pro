# Epic 01 — Tenancy & access

`SDO-TEN-*` — registration, authentication, sessions, RBAC, multi-entity, audit.

Primary diagrams: [UML 02](../diagrams/uml/02-domain-tenancy-rbac.md) ·
[UML 06 §6.1](../diagrams/uml/06-sequences.md) ·
[BPMN 01](../diagrams/bpmn/01-tenant-onboarding.md).

---

### SDO-TEN-01 · Self-service registration creates an entity and its first Admin user

**As a** prospect evaluating SusDevOS
**I want** to register my company and be logged in immediately
**so that** I can start using the product without waiting on anyone.

| | |
|---|---|
| **Status** | 🟡 Partial |
| **Role** | Public (`AllowAny`) |
| **Diagram** | [BPMN 01 — Process](../diagrams/bpmn/01-tenant-onboarding.md) |
| **Code** | `backend/apps/users/views.py` · `SignupView` · `backend/apps/users/services.py` · `register_new_entity()` · `backend/apps/shared/urls_integrations.py` · `CompaniesHouseLookupView` |
| **Tests** | `backend/apps/users/tests/test_api_auth.py::TestSignup` |
| **Linear** | `area:ten` · `type:spec` |

**Acceptance criteria**

1. **Given** a valid `POST /api/auth/signup` body (`first_name`, `last_name`, `email`, `company_name`, `password`, `accepted_terms`),
   **when** it is submitted,
   **then** one `Entities` row (`EntityName=company_name`), one `Users` row (`is_active=True`) holding the `admin` role, and one `EntitySubscriptions` row on the `free` plan are created atomically (`register_new_entity`, `@transaction.atomic`).
2. **Given** a successful signup,
   **when** the response returns,
   **then** it is `201` with an `access_token` body field and a `Set-Cookie: refresh_token` — the new admin is authenticated immediately, with no separate first-login step.
3. **Given** an email already registered,
   **when** `POST /api/auth/signup` is submitted again with it,
   **then** the request is rejected `400` and no second `Users`/`Entities` row is created (`SignupSerializer.validate_email`).
4. **Given** `accepted_terms=False`,
   **when** the signup is submitted,
   **then** it is rejected `400` (`SignupSerializer.validate_accepted_terms`).
5. **Given** the BPMN 01 diagram shows an anonymous prospect calling `POST /api/integrations/companies-house/lookup/` to pre-fill `EntityName`/`EntityType` before submitting `/register`,
   **when** `CompaniesHouseLookupView` is inspected,
   **then** it declares `permission_classes = [IsAuthenticated]` — an anonymous, not-yet-registered visitor cannot reach it, so the pre-fill step the diagram describes has no endpoint a prospect can actually call. This is the reason for the 🟡 status: registration itself is fully built and tested, but the documented Companies House pre-fill path does not exist for the actor the diagram assigns it to.

---

### SDO-TEN-02 · An invited user sets their first password via an emailed onboard link

**As an** invited team member
**I want** to set my own password from the link in my invitation email
**so that** I never have to be handed a password by an administrator.

| | |
|---|---|
| **Status** | 🟡 Partial |
| **Role** | Public (`AllowAny`) for the onboard step; Manager+ to invite |
| **Diagram** | [BPMN 01 — Sub-process: inviting additional users](../diagrams/bpmn/01-tenant-onboarding.md) |
| **Code** | `backend/apps/users/services.py` · `invite_user()` · `backend/apps/users/views.py` · `OnboardView` |
| **Tests** | `backend/apps/users/tests/test_users_permissions.py::TestUsersViewSetEntityResolution::test_manager_can_invite_user_into_tenant` (invite creation only) |
| **Linear** | `area:ten` · `type:spec` |

**Acceptance criteria**

1. **Given** a Manager-or-above calls `POST /api/users/` with `email`, `username`, `FirstName`, `LastName`, `role_key`,
   **when** the request succeeds,
   **then** `invite_user()` creates the `Users` row with `EntityId=request.entity_id` (never from the body), assigns the requested role via `UserRoles`, and creates a `PasswordResetTokens` row with a 7-day expiry — verified by `test_manager_can_invite_user_into_tenant`.
2. **Given** the generated onboard token,
   **when** `POST /api/auth/onboard` is called with `{"token": ..., "new_password": ...}`,
   **then** `OnboardSerializer` rejects an already-used or expired token `400` (same `PasswordResetTokens.is_used`/`is_expired` checks as password reset) — **but no test in the suite exercises `POST /api/auth/onboard` directly**, so this path is unverified by the test suite.
3. **Given** `Users.is_active` defaults to `True` at the model level (`models.py:61`) and `invite_user()` never overrides it,
   **when** an invited user row is created,
   **then** the account is already `is_active=True` before onboarding — `OnboardView.post()` setting `user.is_active = True` on success is a no-op, not the actual activation gate. The only thing preventing login before onboarding is that the account's password is an unguessable `secrets.token_urlsafe(32)` value the invitee does not know. This is untested and diverges from the "invited → onboarded → active" framing in BPMN 01's M3 lane.

---

### SDO-TEN-03 · Logging in with username or email plus password issues a short-lived access token and an HttpOnly refresh cookie

**As a** registered user
**I want** to authenticate once and stay signed in without re-entering my password
**so that** the session is both convenient and hard to steal.

| | |
|---|---|
| **Status** | ✅ Built |
| **Role** | Public (`AllowAny`) |
| **Diagram** | [UML 06 §6.1 — Login, tenant resolution, and refresh](../diagrams/uml/06-sequences.md) |
| **Code** | `backend/apps/users/views.py` · `LoginView` · `backend/apps/users/serializers.py` · `LoginSerializer` · `backend/apps/users/authentication.py` · `issue_tokens()`, `set_refresh_cookie()` |
| **Tests** | `backend/apps/users/tests/test_api_auth.py::TestLogin` |
| **Linear** | `area:ten` · `type:spec` |

**Acceptance criteria**

1. **Given** a request body `{"username": <value>, "password": ...}`,
   **when** `<value>` is either the account's `email` or its `username`,
   **then** both succeed with `200` — the request field is literally named `username` but `LoginSerializer.validate()` tries `authenticate()`, then an `email` lookup, then a `username` lookup, in that order (`test_email_or_username_both_work`).
2. **Given** wrong credentials or a non-existent identifier,
   **when** `POST /api/auth/login` is submitted,
   **then** it returns `400` with `{"code": "invalid_credentials"}` — never `401`, and never revealing which of username/password was wrong.
3. **Given** a user with `is_active=False` or `Status=4`,
   **when** they submit correct credentials,
   **then** login is rejected `400` with `{"code": "account_disabled"}` (`test_disabled_user_returns_400`).
4. **Given** a successful login,
   **when** the response is inspected,
   **then** it carries `access_token` in the body (15-minute JWT, memory-only on the frontend) and sets a `refresh_token` cookie — `HttpOnly`, `SameSite=Lax`, `Path=/api/auth/refresh`, `Max-Age=604800` (7 days) (`set_refresh_cookie`, `test_refresh_cookie_is_set`).

---

### SDO-TEN-04 · The session refreshes silently when the access token expires

**As a** signed-in user
**I want** my session to renew itself in the background
**so that** a 15-minute token lifetime never interrupts my work.

| | |
|---|---|
| **Status** | 🟡 Partial |
| **Role** | Public (`AllowAny`) — the refresh cookie itself is the credential |
| **Diagram** | [UML 06 §6.1 — Access token expires after 15 min](../diagrams/uml/06-sequences.md) |
| **Code** | `backend/apps/users/views.py` · `RefreshView` |
| **Tests** | none found in `backend/apps/users/tests/` |
| **Linear** | `area:ten` · `type:spec` |

**Acceptance criteria**

1. **Given** a `refresh_token` HttpOnly cookie with no `Authorization` header,
   **when** `POST /api/auth/refresh` is called,
   **then** the response is `200` with a new `access_token`, or `401` with `{"code": "no_refresh_token"}` if the cookie is absent.
2. **Given** a refresh token whose `Jti` is present in `RevokedTokens`,
   **when** `POST /api/auth/refresh` is called,
   **then** it is rejected `401` with `{"code": "token_revoked"}`.
3. **Given** the account behind the refresh token has since been deactivated (`is_active=False`),
   **when** `POST /api/auth/refresh` is called,
   **then** it is rejected `401` with `{"code": "account_inactive"}` — this re-check exists specifically because the refresh path never loads the user otherwise, and without it a deactivated account could keep minting access tokens for the remaining 7-day cookie lifetime (see the comment at `views.py:124-127`).
4. None of the three behaviours above has a test in the suite — `RefreshView` has no dedicated test file, so this story is entirely unverified by CI despite being fully implemented.

---

### SDO-TEN-05 · Logging out revokes the token server-side immediately

**As a** user who has just logged out
**I want** my access token to stop working right away
**so that** a stolen or copied token cannot be used after I've signed out.

| | |
|---|---|
| **Status** | ✅ Built |
| **Role** | Authenticated |
| **Diagram** | [UML 02 — Token & credential models](../diagrams/uml/02-domain-tenancy-rbac.md) · [UML 06 §6.1](../diagrams/uml/06-sequences.md) |
| **Code** | `backend/apps/users/views.py` · `LogoutView` · `backend/apps/users/authentication.py` · `RevokedTokenJWTAuthentication.get_validated_token()` |
| **Tests** | `backend/apps/users/tests/test_api_auth.py::TestLogout::test_logout_revokes_access_token` |
| **Linear** | `area:ten` · `type:spec` |

**Acceptance criteria**

1. **Given** an authenticated client with a valid access token,
   **when** `POST /api/auth/logout` is called,
   **then** the token's `Jti` claim is written into `RevokedTokens` (via `get_or_create`, keyed on `Jti`) and the response is `204`.
2. **Given** the same access token is reused after logout,
   **when** any authenticated endpoint is called (e.g. `GET /api/auth/me`),
   **then** `RevokedTokenJWTAuthentication.get_validated_token()` rejects it and the request returns `401` — revocation is immediate, not dependent on the 15-minute expiry (`test_logout_revokes_access_token`).
3. **Given** logout also revokes the refresh cookie/body token when present,
   **when** a raw `refresh_token` is found in the cookie or the request body,
   **then** its `Jti` is separately written to `RevokedTokens`, so the 7-day refresh token is also dead, not just the 15-minute access token.

---

### SDO-TEN-06 · Resetting a forgotten password never reveals whether an account exists

**As a** user who has forgotten my password
**I want** to request a reset link by email
**so that** I can regain access, without an attacker being able to enumerate registered accounts through the same endpoint.

| | |
|---|---|
| **Status** | ✅ Built |
| **Role** | Public (`AllowAny`) |
| **Diagram** | [UML 02 — Token & credential models](../diagrams/uml/02-domain-tenancy-rbac.md) |
| **Code** | `backend/apps/users/views.py` · `ForgotPasswordView`, `ResetPasswordView` |
| **Tests** | `backend/apps/users/tests/test_api_auth.py::TestForgotPassword`, `TestResetPassword` |
| **Linear** | `area:ten` · `type:spec` |

**Acceptance criteria**

1. **Given** `POST /api/auth/forgot-password` with an email that exists,
   **when** compared to the same call with an email that does not exist,
   **then** both return `204` with an identical body — the `Users.DoesNotExist` branch is a silent `pass` (`views.py:210-211`), so the response cannot be used to enumerate accounts (`test_always_returns_204_for_existing_email`, `test_always_returns_204_for_nonexistent_email`).
2. **Given** a valid, unexpired, unused `PasswordResetTokens` row,
   **when** `POST /api/auth/reset-password` is called with `{"token": ..., "new_password": ...}`,
   **then** the password is set, `UsedAt` is stamped, and the user can immediately log in with the new password (`test_valid_token_sets_new_password`).
3. **Given** a token past its `ExpiresAt`, or one whose `UsedAt` is already set,
   **when** it is submitted to `/reset-password`,
   **then** the request is rejected `400` in both cases (`test_expired_token_rejected`, `test_used_token_rejected`) — a used token cannot be replayed.

---

### SDO-TEN-07 · An Admin invites a team member and assigns a role

**As an** entity Admin or Manager
**I want** to invite a colleague and set their role in one step
**so that** they arrive with the correct privileges from day one.

| | |
|---|---|
| **Status** | ✅ Built |
| **Role** | Manager and above (create) |
| **Diagram** | [BPMN 01 — Sub-process: inviting additional users](../diagrams/bpmn/01-tenant-onboarding.md) |
| **Code** | `backend/apps/users/views.py` · `UsersViewSet.get_permissions()` · `backend/apps/users/serializers.py` · `UserCreateSerializer` |
| **Tests** | `backend/apps/users/tests/test_users_permissions.py::TestUsersViewSetAuthorization::test_staff_cannot_invite_user`, `TestUsersViewSetEntityResolution::test_manager_can_invite_user_into_tenant` |
| **Linear** | `area:ten` · `type:spec` |

**Acceptance criteria**

1. **Given** a user holding only the `staff` role,
   **when** they call `POST /api/users/`,
   **then** the request is rejected `403` and no `Users` row with that email is created (`test_staff_cannot_invite_user`) — invitation requires `IsManagerOrAbove`.
2. **Given** a Manager invites a new user with `role_key="staff"`,
   **when** the request succeeds,
   **then** the created user's `EntityId` equals the inviting manager's `request.entity_id` (never a client-supplied value) and the `staff` role is attached via `UserRoles` (`test_manager_can_invite_user_into_tenant`).
3. **Given** `UserCreateSerializer.validate_role_key()`,
   **when** a non-SuperAdmin, non-admin requester (e.g. a Manager) tries `role_key="admin"`,
   **then** it is rejected with `"Only Admins can create Admins."` — a Manager cannot invite a peer Admin.

---

### SDO-TEN-08 · An Admin changes an existing user's role

**As an** entity Admin
**I want** to change a team member's role
**so that** their privileges reflect a change in responsibility.

| | |
|---|---|
| **Status** | ✅ Built |
| **Role** | Entity Admin (`IsEntityAdmin`) |
| **Diagram** | [UML 02 — RolePrivileges / UserRoles](../diagrams/uml/02-domain-tenancy-rbac.md) |
| **Code** | `backend/apps/users/views.py` · `UsersViewSet.assign_role()` |
| **Tests** | `backend/apps/users/tests/test_users_permissions.py::test_staff_cannot_self_assign_admin_role`, `test_admin_can_change_role` |
| **Linear** | `area:ten` · `type:spec` |

**Acceptance criteria**

1. **Given** a staff member,
   **when** they `PATCH /api/users/{their_own_id}/role/` with `{"role_key": "admin"}`,
   **then** the request is rejected `403` and their role is unchanged — self-escalation via a direct API call is blocked even though the UI control is only client-side hidden (`test_staff_cannot_self_assign_admin_role`).
2. **Given** an Admin changes another user's role,
   **when** `PATCH /api/users/{id}/role/` succeeds,
   **then** it returns `204`, the target's prior active `UserRoles` row(s) are set to `Status=4` (retired) and a new `UserRoles` row is created — both steps run inside `transaction.atomic()` so the retire-then-create pair cannot interleave with a concurrent request (`assign_role`, `test_admin_can_change_role`).
3. **Given** `role_key` names a role that does not exist or is inactive,
   **when** `PATCH .../role/` is called,
   **then** it returns `400` with `{"code": "not_found"}` and no `UserRoles` row is touched.

---

### SDO-TEN-09 · An Admin grants or revokes a single privilege for one user

**As an** entity Admin
**I want** to grant or withdraw one specific privilege on top of a user's role
**so that** I can make a narrow exception without redesigning the role system.

| | |
|---|---|
| **Status** | ✅ Built |
| **Role** | Entity Admin (`IsEntityAdmin`) |
| **Diagram** | [UML 02 — RBAC §Privilege resolution algorithm](../diagrams/uml/02-domain-tenancy-rbac.md) |
| **Code** | `backend/apps/users/views.py` · `UsersViewSet.add_override()`, `remove_override()` · `backend/apps/shared/permissions.py` · `_resolve_privilege()` |
| **Tests** | `backend/apps/users/tests/test_users_permissions.py::test_staff_cannot_grant_privilege_override`, `test_staff_cannot_remove_privilege_override` |
| **Linear** | `area:ten` · `type:spec` |

**Acceptance criteria**

1. **Given** a staff member,
   **when** they `POST /api/users/{id}/privileges/override/`,
   **then** the request is rejected `403` and no `UserPrivilegeOverrides` row is created (`test_staff_cannot_grant_privilege_override`) — granting/removing overrides is Admin-only, mirroring `assign_role`.
2. **Given** an active `UserPrivilegeOverrides` row exists limiting a user (`OverrideAction=2`, Revoke),
   **when** a staff member calls `DELETE /api/users/{id}/privileges/override/{override_id}/`,
   **then** the request is rejected `403` and the override still exists — removing a restriction is itself a privileged action, not just adding one (`test_staff_cannot_remove_privilege_override`).
3. **Given** `_resolve_privilege()`'s override branch,
   **when** both a Grant (`OverrideAction=1`) and a Revoke (`OverrideAction=2`) override exist for the same user and interface,
   **then** the query `order_by("-OverrideAction")` returns the Revoke row first (`2` sorts before `1` descending) and it wins — this ordering is load-bearing and undocumented outside the code comment at `permissions.py:83`.

---

### SDO-TEN-10 · Privilege resolution unions all of a user's active roles

**As a** platform operator
**I want** a user with two active roles to hold the privileges of both
**so that** a role assignment never silently disappears depending on database row order.

| | |
|---|---|
| **Status** | ✅ Built |
| **Role** | n/a (internal resolution logic) |
| **Diagram** | [UML 02 §Privilege resolution algorithm](../diagrams/uml/02-domain-tenancy-rbac.md) — see finding [F2](../diagrams/FINDINGS.md#f2) |
| **Code** | `backend/apps/shared/permissions.py` · `_resolve_privilege()` |
| **Tests** | `backend/apps/users/tests/test_users_permissions.py::TestResolvePrivilegeMultiRole::test_two_active_roles_union_their_privileges` |
| **Linear** | `area:ten` · `type:bug` |

**Acceptance criteria**

1. **Given** a user holds two simultaneously active `UserRoles` rows (`manager` and `staff`),
   **when** `_resolve_privilege(user, interface_key, permission_type)` is called for an interface only `manager`'s `RolePrivileges` grants, and separately for one only `staff`'s grants,
   **then** both calls return `True` — resolution is the union across `RoleId__in=role_ids`, not an arbitrary `.first()` row (`test_two_active_roles_union_their_privileges`). Before this fix (finding F2), exactly one of the two assertions would fail depending on which `UserRoles` row the database happened to return first.
2. **Given** no `UniqueConstraint` was added on `(UserId, Status=1)`,
   **when** multiple active roles exist for a user,
   **then** this remains a supported, well-defined state rather than a database error — the deliberate choice recorded in F2's resolution note, made because such a constraint could fail against pre-existing duplicate rows.

---

### SDO-TEN-11 · A consultant with access to several client entities switches between them via the X-Entity-ID header

**As an** ESG consultant serving multiple clients
**I want** to switch which client entity I'm operating in
**so that** I can serve several clients from one account without duplicate logins.

| | |
|---|---|
| **Status** | 🟡 Partial |
| **Role** | Authenticated; SuperAdmin for granting membership |
| **Diagram** | [BPMN 01 — Sub-process: multi-entity access](../diagrams/bpmn/01-tenant-onboarding.md) |
| **Code** | `backend/apps/entities/middleware.py` · `TenantQueryMiddleware` · `backend/apps/shared/views.py` · `resolve_request_entity_id()` · `backend/apps/entities/services.py` · `user_can_access_entity()`, `accessible_entity_ids()` · `backend/apps/entities/views.py` · `EntitiesViewSet.members()`, `.accessible()` |
| **Tests** | `backend/apps/emissions/tests/test_tenant_isolation.py::TestHeaderSpoofing` (spoof-rejection only) |
| **Linear** | `area:ten` · `type:spec` |

**Acceptance criteria**

1. **Given** a user with an `EntityMembers` grant for a second entity,
   **when** they send `X-Entity-ID: <that entity's id>` on any request,
   **then** `user_can_access_entity()` allows it and `request.entity_id` resolves to the requested entity — but **no test in the suite exercises the success path**: `test_tenant_isolation.py::TestHeaderSpoofing` only proves rejection of an entity the user does *not* belong to, never acceptance of one granted via `EntityMembers`.
2. **Given** `EntitiesViewSet.members()` (`POST /api/entities/{id}/members/`),
   **when** a SuperAdmin grants a user access via `UserId` or `email`,
   **then** an `EntityMembers` row is created — this endpoint, and `GET /api/entities/accessible/` (the entity-switcher data source), have **zero test coverage** in `backend/apps/entities/tests/`.
3. **Given** a request with no `X-Entity-ID` header,
   **when** it is processed,
   **then** `request.entity_id` falls back to `Users.EntityId_id` — the user's home entity (`resolve_request_entity_id`, tested indirectly by every tenant-scoped test that omits the header).

---

### SDO-TEN-12 · Every tenant-scoped query is filtered by entity, and EntityId is never accepted from a request body

**As a** platform operator
**I want** every domain query to be scoped to the caller's resolved entity
**so that** one tenant can never read or write another tenant's data, regardless of what the client sends.

| | |
|---|---|
| **Status** | ✅ Built |
| **Role** | Authenticated |
| **Diagram** | [UML 06 §6.1 — Subsequent authenticated request](../diagrams/uml/06-sequences.md) |
| **Code** | `backend/apps/shared/views.py` · `TenantViewSetMixin`, `EntityScopeInitialMixin`, `resolve_request_entity_id()` · `backend/apps/entities/middleware.py` · `TenantQueryMiddleware` |
| **Tests** | `backend/apps/emissions/tests/test_tenant_isolation.py` (full suite) |
| **Linear** | `area:ten` · `type:spec` |

**Acceptance criteria**

1. **Given** `TenantQueryMiddleware` runs *before* DRF authentication (Django middleware ordering), so `request.user` is still `AnonymousUser` when it executes for a JWT request,
   **when** the middleware sets `request.entity_id`,
   **then** it is left `None` for JWT requests — every tenant-scoped `ViewSet` must therefore mix in `EntityScopeInitialMixin`, whose `initial()` calls `resolve_request_entity_id()` *after* `super().initial()` has run DRF authentication, to re-resolve `request.entity_id` from the now-authenticated user. Without this mixin, `get_queryset()` returns `Model.objects.none()` for every non-SuperAdmin (documented explicitly in the comment at `apps/users/views.py:307-312`).
2. **Given** two entities each with their own emissions record,
   **when** entity A's client calls `GET /api/emissions/`,
   **then** entity B's record never appears in the results, in either direction (`TestListIsolation::test_both_entities_see_only_their_own`).
3. **Given** a client submits `EntityId` in the POST body pointing at a different entity,
   **when** `TenantViewSetMixin.perform_create()` runs,
   **then** the created row's `EntityId` is forced to `request.entity_id`, ignoring the body value entirely (`test_entity_id_not_accepted_from_request_body`, `test_entity_id_always_from_header_not_body`).
4. **Given** a request for another entity's record by primary key (not via list),
   **when** `GET`/`PATCH`/`DELETE` is called on that id,
   **then** it returns `404`, not `403` — the row is invisible, not merely forbidden (`TestDetailIsolation`).

---

### SDO-TEN-13 · SuperAdmin may act on any entity

**As a** SuperAdmin
**I want** to operate in any tenant's context
**so that** I can provide platform-level support and administration.

| | |
|---|---|
| **Status** | ✅ Built |
| **Role** | SuperAdmin |
| **Diagram** | [BPMN 01 — Sub-process: multi-entity access](../diagrams/bpmn/01-tenant-onboarding.md) |
| **Code** | `backend/apps/shared/views.py` · `resolve_request_entity_id()` (`IsSuperAdmin` bypass branch) · `backend/apps/shared/permissions.py` · every `SUPERADMIN_BYPASS`-tagged check |
| **Tests** | `backend/apps/entities/tests/test_api.py::TestEntitiesList::test_superadmin_sees_all_entities` |
| **Linear** | `area:ten` · `type:spec` |

**Acceptance criteria**

1. **Given** a SuperAdmin sends any `X-Entity-ID` header value, including one for an entity they hold no `EntityMembers` grant for,
   **when** `resolve_request_entity_id()` runs,
   **then** `request.entity_id` is set to that value unconditionally — the `user_can_access_entity()` membership check is skipped entirely for `IsSuperAdmin=True` users.
2. **Given** `GET /api/entities/`,
   **when** called by a SuperAdmin versus an entity Admin,
   **then** the SuperAdmin sees every active entity (`Status__lt=4`, no `EntityId` filter) while the Admin sees only their own entity plus related branches (`test_superadmin_sees_all_entities`, `test_admin_sees_only_own_entity`).
3. **Given** `build_privilege_map()`,
   **when** called for a SuperAdmin,
   **then** every interface resolves `True` without consulting `RolePrivileges`/`UserPrivilegeOverrides` at all (`test_superadmin_gets_all_privileges_true`).

---

### SDO-TEN-14 · Entity hierarchy and related entities

**As a** group-structure Admin
**I want** to model parent/subsidiary and peer relationships between entities
**so that** consolidated GHG reporting can roll subsidiaries up into a parent.

| | |
|---|---|
| **Status** | 🟡 Partial |
| **Role** | Entity Admin / SuperAdmin |
| **Diagram** | [UML 02 — Tenancy](../diagrams/uml/02-domain-tenancy-rbac.md) |
| **Code** | `backend/apps/entities/models.py` · `Entities.ParentEntityId`, `RelatedEntities` · `backend/apps/entities/views.py` · `EntitiesViewSet.get_queryset()`, `.consolidated_emissions()` · `backend/apps/entities/services.py` · `compute_consolidated_emissions()` |
| **Tests** | none found for hierarchy/consolidation in `backend/apps/entities/tests/` |
| **Linear** | `area:ten` · `type:spec` |

**Acceptance criteria**

1. **Given** an entity Admin,
   **when** `GET /api/entities/` is called,
   **then** the visible set is the caller's own entity plus every entity where a `RelatedEntities` row names it as `ChildEntityId` under the caller's entity as `ParentEntityId` (`get_queryset()`, `related_ids` via `child_relations`) — **this branch is not covered by a test**; `test_admin_sees_only_own_entity` only proves an *unrelated* entity is excluded, not that a *related* one is included.
2. **Given** `Entities.ParentEntityId` (a self-referential FK distinct from the `RelatedEntities` junction table),
   **when** `compute_consolidated_emissions()` rolls up subsidiaries,
   **then** it queries `Entities.objects.filter(ParentEntityId=entity)`, not `RelatedEntities` — the two hierarchy mechanisms (`ParentEntityId` for consolidation, `RelatedEntities` for the entity list's visibility) are separate and can diverge; nothing in the code keeps them in sync.
3. **Given** `GET /api/entities/{id}/consolidated-emissions/`,
   **when** called with `?approach=1` (Equity Share) versus omitted (defaults to the entity's own `ConsolidationApproach`, else Operational Control),
   **then** subsidiary contributions are scaled by `OwnershipSharePercent/100` for Equity Share and by `100%` for Financial/Operational Control (`compute_consolidated_emissions`) — **this entire endpoint has no test**.

---

### SDO-TEN-15 · Per-entity API keys are deferred during PMF

**As a** product and security owner
**I want** customer-managed API credentials disabled during the PMF phase
**so that** the application exposes only the first-party JWT-authenticated API surface.

| | |
|---|---|
| **Status** | ⏸ Deferred by product decision (2026-08-25) |
| **Role** | None — no customer-accessible route |
| **Diagram** | [UML 02 — Token & credential models](../diagrams/uml/02-domain-tenancy-rbac.md) |
| **Code** | Dormant models/services retained; no view action or API-key authenticator is registered |
| **Tests** | `backend/apps/entities/tests/test_api.py::TestRetiredApiKeyRoutes` |
| **Linear** | `area:ten` · `type:spec` |

**Acceptance criteria**

1. **Given** any anonymous or authenticated caller, **when** an old API-key list, create, or
   revoke path is requested, **then** it returns `404` and changes no key data.
2. **Given** the settings application, **when** it is built, **then** there is no API-key page,
   navigation entry, or generated client operation.
3. **Given** historical API-key rows, **when** the retirement migration runs, **then** the rows
   and hashes are retained but every key is soft-revoked (`Status=4`).

---

### SDO-TEN-16 · Actions are recorded in the audit log under a retention tier

**As a** compliance officer
**I want** every mutating action recorded with a defensible retention period
**so that** the platform can support a regulatory audit (Cyber Essentials / ISO 27001 roadmap, `spec/compliance.md`).

| | |
|---|---|
| **Status** | 🟡 Partial |
| **Role** | n/a (system-level) |
| **Diagram** | [UML 02 — Token & credential models](../diagrams/uml/02-domain-tenancy-rbac.md) |
| **Code** | `backend/apps/shared/audit.py` · `audit_log()` · `backend/apps/shared/views.py` · `TenantViewSetMixin._audit()` |
| **Tests** | `backend/apps/emissions/tests/test_api.py::TestUnlock::test_unlock_writes_audit_log` (tier-3 unlock path only) |
| **Linear** | `area:ten` · `type:spec` |

**Acceptance criteria**

1. **Given** `audit_log()`'s `retention_tier` parameter,
   **when** no value is passed,
   **then** it defaults to `3` (7-year, regulatory) — every `TenantViewSetMixin.perform_create()`/`perform_update()`/`perform_destroy()` call across every tenant-scoped ViewSet therefore writes a 7-year-retention row by default, per the docstring's stated rationale ("CRUD on domain records is regulatory evidence").
2. **Given** an emissions record is unlocked via `POST /api/emissions/{id}/unlock/`,
   **when** the unlock succeeds,
   **then** an `AuditLog` row is written with `Action="Unlock_Verified"` and `RetentionTier=3` (`test_unlock_writes_audit_log`) — the only retention-tier assertion anywhere in the test suite.
3. **Given** `audit_log()` wraps its `AuditLog.objects.create()` call in a bare `try/except`,
   **when** the write itself fails for any reason,
   **then** the exception is logged (`logger.error`) and swallowed — an audit-log failure never breaks the underlying business operation. **No test forces this failure path**, so the "audit failure must not break the request" guarantee is unverified.
4. **Given** the three-tier scheme documented in `audit.py`'s module docstring (1 = 30-day, 2 = 1-year auth/session, 3 = 7-year CRUD/regulatory),
   **when** the codebase is searched for tier-1 and tier-2 call sites,
   **then** none were found passing `retention_tier=1` or `retention_tier=2` explicitly — every observed call site either omits the parameter (defaulting to 3) or passes `3` explicitly. The shorter retention tiers are declared but appear unused, which is worth confirming is intentional rather than a missed wiring.
