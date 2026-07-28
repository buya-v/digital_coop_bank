"""Member self-service profile (EP-1, 04 §3.1) — getMyProfile / updateMyProfile.

Operates ONLY on the authenticated Member resolved by `get_current_member` (the
token subject IS the identity). There is no member id in any path or body, so a
member can only ever read or write THEIR OWN profile — the IDOR class is
structurally excluded, not merely checked.

Field ownership (reconciled with ProfilePatchRequest + the MemberProfile schema):

- EDITABLE by the member: the three DEC-6 name parts, the structured postal
  address, and the contact channels (email / phone_number).
- READ-ONLY (attempting to set any -> 422): `legal_name` (DERIVED from the name
  parts, never stored), `mrz_name_latin` (KYC-populated, verbatim MRZ),
  `registration_number` (the identity key; a change needs KYC step-up, which is a
  later slice — so it is not member-editable here), and `member_id` (system-owned
  public id). `id` (the UUID PK) is likewise never writable.

Like the slice-1/2 services this NEVER commits — the router owns the transaction
boundary; the service mutates the attached Member and the router commits.
"""
from __future__ import annotations

from app.models.membership import Member

# Member-editable profile attributes (names → attribute on Member).
EDITABLE_FIELDS: frozenset[str] = frozenset(
    {
        "ner",
        "etsgiin_ner",
        "ovog",
        "address_line_1",
        "address_line_2",
        "city",
        "region",
        "postal_code",
        "country",
        "email",
        "phone_number",
    }
)

# Attributes that MAY appear in a request but are never member-writable. Each maps
# to the canonical 422 error code the contract/04 §3.1 pin for it.
READ_ONLY_FIELD_CODES: dict[str, str] = {
    "legal_name": "LEGAL_NAME_NOT_EDITABLE",
    "mrz_name_latin": "MRZ_NAME_NOT_EDITABLE",
    "registration_number": "REGISTRATION_NUMBER_NOT_EDITABLE",
    "member_id": "MEMBER_ID_NOT_EDITABLE",
    "id": "FIELD_NOT_EDITABLE",
}


class ProfileError(Exception):
    """Base for profile domain errors (mapped to HTTP by the router)."""


class ProfileFieldNotEditable(ProfileError):
    """A read-only / derived / system-owned field was supplied (maps to 422)."""

    def __init__(self, field: str, code: str) -> None:
        super().__init__(f"Field '{field}' is not member-editable.")
        self.field = field
        self.code = code


class ProfileFieldUnknown(ProfileError):
    """An unrecognised field was supplied (maps to 422 VALIDATION_FAILED)."""

    def __init__(self, field: str) -> None:
        super().__init__(f"Unknown profile field '{field}'.")
        self.field = field


class ProfileService:
    """Read + update the authenticated member's own profile."""

    def apply_update(self, member: Member, provided: dict[str, object]) -> bool:
        """Apply a validated PATCH to `member` in place.

        `provided` is the caller's supplied fields (a pydantic
        `model_dump(exclude_unset=True)` — only keys the client actually sent).
        Raises `ProfileFieldNotEditable` for a read-only field and
        `ProfileFieldUnknown` for an unrecognised one, BEFORE mutating anything
        (validate-then-apply, so a rejected PATCH leaves the member untouched).

        Returns whether any KYC-relevant field (name / address / contact) changed,
        which the router surfaces as `reverification_required`.
        """
        for field in provided:
            if field in READ_ONLY_FIELD_CODES:
                raise ProfileFieldNotEditable(field, READ_ONLY_FIELD_CODES[field])
            if field not in EDITABLE_FIELDS:
                raise ProfileFieldUnknown(field)

        changed = False
        for field, value in provided.items():
            if getattr(member, field) != value:
                changed = True
            setattr(member, field, value)
        return changed
