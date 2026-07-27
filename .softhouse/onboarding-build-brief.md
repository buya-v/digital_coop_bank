# Build brief — Onboarding application vertical (EP-1, slice 1)

First real FEATURE build. Delivers the resumable onboarding-application draft
(create / get / update) and the persistence→service→router foundation it forces.
Blocker-free: NO money movement, NO ledger, NO ХУР/state-register call, NO share
purchase. Those are later slices.

## Standing project facts (CLAUDE.md)
- Money = integer minor units, MNT, never float. (No money in this slice, but the
  MoneyMinor type and non-negotiable stand.)
- Names are THREE fields — ovog / etsgiin_ner (patronymic) / ner (given). Never
  first_name/last_name. registration_number = 10 chars (2 Cyrillic + 8 digits),
  structural validation only (check-digit algorithm unpublished — do NOT invent one).
- Two time zones, no DST; dates y.MM.dd. Never hardcode an offset.
- PO direction (provisional): common bond = defined-bond SCC path (eligibility check
  is config-driven — `eligibility.common_bond_rules`); eKYC = ХУР/XYP state-register
  (NOT in this slice); self-host only. Onboarding does NOT create a member in a
  rejected status (DEC-4).

## Scope of THIS slice
Implement, against the EXISTING OpenAPI contract `backend/openapi/paths/ep1-identity.yaml`
+ `schemas/ep1-identity.yaml` (schemas OnboardingApplicationCreateRequest/Response/
Current/PatchRequest/PatchResponse), these operations ONLY:
- `createOnboardingApplication` (POST /onboarding/applications) — pre-auth bootstrap.
- `getCurrentOnboardingApplication` (GET) — the applicant's in-progress draft.
- `updateCurrentOnboardingApplication` (PATCH) — save DEC-6 identity step data.

DEFERRED to slice 2 (do NOT build now): `checkOnboardingEligibility`, `createKycSession`,
`getKycStatus`, MFA/step-up, devices, profile, consents.

## Data model (T1 resolves against 04 + the contract)
There is currently NO OnboardingApplication table (models: Member, KycSubmission,
DeviceBinding, ConsentRecord, MembershipShare). Read `04_technical_architecture.md`
§2 (the E-* entity for onboarding) AND the OpenAPI OnboardingApplication schemas and
RECONCILE:
- Preferred: a distinct `onboarding_application` entity — the resumable DRAFT holding
  the DEC-6 identity fields (ovog/etsgiin_ner/ner, mrz_name_latin, registration_number,
  structured address) + a status (e.g. DRAFT / SUBMITTED) + created/updated. It is
  promoted to a `Member` later (on KYC approval, a future slice) — NOT in this slice.
- If 04 models onboarding as the Member-in-PENDING_KYC instead, FOLLOW 04 + the
  contract and say so. Do not invent fields the contract/04 don't define.
- Whatever you add to the model, add to `migrations/versions/0001_initial.py` in the
  SAME change (check_migration asserts metadata DDL == migration DDL). Nothing is
  deployed, so extending 0001 is correct (do not create 0002).

## Foundation to establish (first feature — set the pattern well)
- Repository layer: a small generic `BaseRepository` over a Session (get / add /
  get-for-update as needed) + an `OnboardingApplicationRepository`.
- Service layer: an `OnboardingService` holding the create/get/update logic (status
  transitions, DEC-6 validation, registration_number STRUCTURAL validation only).
- API layer: a FastAPI router `app/api/routers/onboarding.py` using `Depends(get_session)`
  (the T1 persistence dep already exists). Wire it into `app/main.py`.
- Pre-auth bootstrap: create returns an `application_id` + a bootstrap token; get/update
  identify the draft by that token (a minimal application-scoped token — NOT full auth/
  MFA, which is a later slice). Keep it simple and documented; do not build a full JWT/
  session stack.
- Response/request shapes MUST match the OpenAPI schemas (property names, required
  fields, enums). If a schema and 04 disagree, flag it — don't silently pick.

## Non-negotiables & gates
- No float anywhere. No first_name/last_name. No hardcoded tz offset. No invented
  registration check-digit. No ХУР/ledger/money call.
- Gates (run from backend/, ALL must PASS): `python3 -m app.db.check_models`,
  `python3 -m app.db.check_migration`, `python3 -m pytest -q` (add tests for the 3
  endpoints via TestClient with the session dependency overridden — NO real DB),
  and `python3 openapi/validate.py` stays PASS (you may extend the spec only if a
  gap is found; prefer implementing to the existing contract).
- mypy strict + ruff clean on new files.

## Handoff
List: the data-model decision (+ 04 reconciliation), every new file, the endpoints
implemented with their contract conformance, the bootstrap-token approach, and all
gate outputs verbatim.
