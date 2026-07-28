# Build brief — Member auth foundation + profile self-service (EP-1)

Builds on the onboarding vertical. Adds the member-authentication foundation
(verify external-IdP Bearer JWTs → `get_current_member`) and the first post-auth
self-service endpoints (getMyProfile / updateMyProfile). Unblocks every future
member-facing endpoint. Still NO money/ledger.

## The auth model (from the contract root.yaml `memberOAuth2`)
- Members authenticate via an **external, operator-chosen OIDC/OAuth2 IdP** (endpoints
  are placeholders — self-host/data-residency, 04 §5.3). Access tokens are **RS256-signed
  JWTs, lifetime ≤ 15 min**, presented as `Authorization: Bearer <JWT>`; refresh tokens
  bind to DeviceBindings.
- **This backend VERIFIES tokens; it does NOT issue them.** Build a JWT VERIFIER behind a
  port (verify against the IdP's public key / JWKS) + a **dev/test signer** (an RS keypair
  used ONLY in dev/tests to mint tokens so the suite can exercise the endpoints). The real
  IdP + its keys are operator-config; do not pin a real IdP.

## SECURITY REQUIREMENTS (this is a security-critical component — the review will attack it)
- Verify the signature with the IdP public key. **Only accept `alg: RS256`** (the configured
  algorithm). **REJECT `alg: none` and REJECT HS256** (algorithm-confusion / key-confusion
  attacks) — never let the token header pick the algorithm/key class.
- Enforce `exp` (expiry), and `iss` (issuer) + `aud` (audience) if the contract/config
  provides them. Reject expired, not-yet-valid (`nbf`), wrong-issuer, wrong-audience.
- Resolve the member from the token subject (`sub`) → a Member row; 401 on a missing/invalid
  token, 401/403 on an unknown/invalid subject. Do NOT trust any claim as a member fact
  beyond the verified subject → DB lookup.
- Never log the token or its claims verbatim. No secret/keypair committed except a
  clearly-marked DEV-ONLY test key used solely by tests.
- Add the JWT dependency to pyproject (PyJWT with the crypto extra, or equivalent);
  prefer a well-known library over hand-rolled crypto.

## Member model extension (for the profile) — model + migration in LOCKSTEP
`MemberProfile` (schemas/ep1-identity.yaml) needs fields Member lacks. Add to Member the
contract-required profile fields, reconciled with 04 §2.2 E-1: the member-facing
`member_id` (non-guessable public id, e.g. `DCB-XXXXXXXX`, DEC-28), structured postal
address (address_line_1/2, city, region, postal_code, country), email, phone_number,
preferred_language (Cyrillic-Mongolian default per CLAUDE.md), and any other REQUIRED
MemberProfile property. `legal_name` is DERIVED read-only (never a stored editable column;
editing it → 422 LEGAL_NAME_NOT_EDITABLE). Do NOT invent fields the schema/04 don't define.
- Wire PROMOTION (services/kyc.py `_promote`) to populate the new Member fields from the
  draft (email/phone/address) and to generate the public `member_id`. Keep the DEC-4
  guarantee intact.

## Endpoints (to the EXISTING contract)
- `getMyProfile` (GET /api/v1/members/me, 200 MemberProfile) — the authenticated member's
  profile; `legal_name` derived.
- `updateMyProfile` (PATCH, 200) — update the member-editable fields only. Attempting to set
  `legal_name`, `mrz_name_latin`, `registration_number`, or `member_id` → 422 (they are
  KYC/derived/system-owned, not member-editable). Confirm the editable set against the schema.

## Scope / out of scope
- IN: auth foundation (verify + get_current_member + dev signer), Member profile extension +
  promotion wiring, getMyProfile/updateMyProfile, tests.
- OUT (later slices): MFA enrollment / step-up token (auth-server-entangled), devices
  list/revoke, consents list/upsert, share purchase (ledger), any money.
- Reuse the slice-1/2 foundation (repositories/services/routers/Error envelope). Repos
  flush-not-commit; routers commit on mutation. get_current_member is a new dependency
  alongside the pre-auth bootstrap-token dep (keep both; onboarding stays pre-auth).

## Gates (from backend/, ALL PASS; paste outputs)
`python3 -m app.db.check_models`, `python3 -m app.db.check_migration` (Member extension
lockstep), `python3 openapi/validate.py`, `python3 -m pytest -q` (tests: valid token →
profile; expired/bad-sig/alg-none/HS256 → 401; unknown subject → 401/403; PATCH editable
field persists; PATCH a read-only field → 422). ruff + mypy strict clean on new files.

## Handoff
The verifier/port design + the exact algorithm/claim checks enforced (and the attacks
rejected); the dev-signer (test-only) approach; the Member extension + promotion wiring +
the DEC-4-still-holds note; endpoint conformance; all gate outputs verbatim.
