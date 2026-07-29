"""Deterministic in-memory MOCK of the SMS delivery port.

No network, no vendor SDK — it simply RECORDS every code it was asked to deliver,
so a test can read back the exact code the enrollment "sent" and drive the binding
flow deterministically (the brief: "the mock lets tests drive the code"). This
mirrors the ХУР/XYP `MockEkycProvider` pattern.

`unavailable=True` makes it raise `SmsDeliveryError` so the delivery-failure branch
is exercisable. State is per-instance and in-memory; a single instance is reused
across the app/test so the sent codes are inspectable.
"""
from __future__ import annotations

import dataclasses

from app.adapters.sms.port import SmsDeliveryError, SmsSender


@dataclasses.dataclass(frozen=True)
class SentSms:
    """A record of one delivered code (test-inspectable)."""

    phone_number: str
    code: str


class MockSmsSender(SmsSender):
    """Records delivered codes instead of hitting a real SMS gateway."""

    def __init__(self, *, unavailable: bool = False) -> None:
        self._unavailable = unavailable
        self.sent: list[SentSms] = []

    def send_verification_code(self, *, phone_number: str, code: str) -> None:
        if self._unavailable:
            raise SmsDeliveryError("SMS gateway unreachable")
        self.sent.append(SentSms(phone_number=phone_number, code=code))

    @property
    def last_code(self) -> str | None:
        """The most recently delivered code, or None (test convenience)."""
        return self.sent[-1].code if self.sent else None
