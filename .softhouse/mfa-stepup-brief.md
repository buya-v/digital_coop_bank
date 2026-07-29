# Build brief — MFA enrollment + step-up (EP-1, security-critical)

The final substantial EP-1 slice. The backend now ISSUES a security credential (the
single-use step-up token) and STORES an MFA secret (TOTP seed). Treat both as
security-critical — the reviews will attack them. No money/ledger.

## Contract (root.yaml + ep1-identity.yaml)
- `MfaFactorType` enum: **TOTP, SMS**.
- `createMfaEnrollment` (POST /api/v1/auth/mfa/enrollments, memberOAuth2, 201
  MfaEnrollmentResponse{ ..., binding_challenge }): enroll a factor for the current
  member; returns a binding challenge (TOTP: the shared secret / otpauth URI to bind;
  SMS: a sent code). 409 on an already-enrolled/duplicate factor; 422 on a bad request.
- `createStepUpToken` (POST /api/v1/auth/step-up, memberOAuth2, 200 StepUpResponse{
  step_up_token, expires_at }): verify `factor_response` (e.g. a TOTP code) for the
  current member's factor; mint a **single-use, short-lived** step_up_token bound to the
  member (and the optional `requested_action`). **423 Locked** on too many failed attempts.
- `stepUpAssertion` security scheme: apiKey header **`X-Step-Up-Token`**, required IN
  ADDITION to memberOAuth2 for sensitive actions. Consumed single-use.

## SECURITY REQUIREMENTS (the reviews will attack these)
### MFA factor + secret
- New `mfa_factor` model + migration (LOCKSTEP): member_id, factor_type, status
  (PENDING → ACTIVE after binding), the TOTP secret, timestamps. A member's factor set
  is per-(member,type); 409 on duplicate active enrollment.
- **The TOTP secret MUST be encrypted at rest** — never stored plaintext. Use app-level
  authenticated encryption (Fernet / AES-GCM from the already-present `cryptography`
  lib) with a key from config/env (operator-supplied; never committed). Store the
  ciphertext; decrypt only in-memory to verify a code. Document the key-management
  caveat (a KMS in production). No secret/key in logs, ever.
- Use a well-known TOTP implementation (add `pyotp` to pyproject) — do NOT hand-roll
  TOTP. SMS: put delivery behind a PORT + a deterministic MOCK (no real SMS provider in
  dev), same pattern as ХУР; the mock lets tests drive the code. TOTP is the primary
  real factor.
- Enrollment binding: a PENDING factor becomes ACTIVE only after the member proves a
  correct code (a confirm step or first successful step-up). A never-confirmed factor
  must not authorize step-up. Decide + document against the contract.

### Step-up token (the backend issues a credential — highest risk)
- **Single-use**: prefer an OPAQUE random token stored server-side (a `step_up_token`
  table: token_hash, member_id, requested_action, expires_at, consumed_at) so
  consumption is a DB fact, not a stateless-JWT JTI dance. Store only the HASH.
- **Short-lived**: a few minutes max (`expires_at` returned); reject expired.
- **Bound to the member**: a step-up token minted for member A must NEVER authorize a
  step-up action for member B. The require_step_up dependency verifies: token exists +
  not expired + not consumed + belongs to get_current_member; then CONSUMES it (mark
  consumed_at) so a replay fails. If `requested_action` was set, the consuming operation
  must match it.
- **Lockout**: track failed factor_response attempts; after a threshold return **423
  Locked** (do not allow unlimited TOTP guessing). Constant-time compare where relevant.
- TOTP verification must allow only a small time window (±1 step) — no wide drift.

### require_step_up dependency
- A FastAPI dependency that reads `X-Step-Up-Token`, verifies + consumes it (single-use,
  member-bound, unexpired), and 401/403 otherwise. Compose it with get_current_member.

## Wire the now-unblocked sensitive op
- **revokeDevice** (DELETE /api/v1/auth/devices/{id}, memberOAuth2 + stepUpAssertion):
  now buildable. Mount it, gated by BOTH get_current_member AND require_step_up; IDOR —
  a member can only revoke THEIR OWN device (404, not another member's device, by id).
  Add it to the route allowlist (test_health) since it is now expected.
- Optionally wire the profile `registration_number` edit behind step-up (it currently
  422s) — OR leave that for later and keep 422; state your choice. Do NOT build the
  full re-KYC flow.

## Scope / out
- IN: mfa_factor model+migration, createMfaEnrollment (TOTP real + SMS mock port),
  createStepUpToken + step_up_token store + require_step_up dep, revokeDevice, tests.
- OUT: real SMS provider, WebAuthn, biometric, share purchase / money / ledger, the
  full re-KYC reg-number flow.
- Reuse the foundation (get_current_member, repos flush / router commits, Error envelope).

## Gates (from backend/, ALL PASS; the orchestrator installs new deps — pyotp — before
verifying)
check_models, check_migration (mfa_factor + step_up_token lockstep), openapi/validate.py,
pytest. Tests MUST include: TOTP enroll→confirm→step-up happy path; wrong code rejected;
lockout after N failures → 423; step-up token single-use (second use fails); expired
token rejected; a token for member A rejected for member B (binding); revokeDevice needs
step-up (401/403 without it) and is IDOR-safe; secret is never returned/logged in
plaintext beyond the enrollment binding_challenge. ruff+mypy strict clean on new files.

## Handoff
The factor/secret model + the encryption approach (+ key-mgmt caveat); the step-up token
design (opaque+DB single-use, member binding, expiry, lockout); the TOTP window; the
require_step_up dep; the revokeDevice wiring + IDOR; every security control and which
attack each test proves; gate outputs verbatim.
