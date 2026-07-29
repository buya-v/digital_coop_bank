"""SMS delivery port + implementations (MFA / step-up one-time codes).

An SMS MFA factor delivers a one-time code out-of-band. The gateway is an operator
procurement decision (no vendor pinned), so the app depends on `SmsSender` (the
port) and this slice ships `MockSmsSender` (a deterministic, no-network stub that
records sent codes for tests). Swapping in a real gateway is a new implementation
of the same port, not a change to the enrollment service.
"""
from app.adapters.sms.mock import MockSmsSender, SentSms
from app.adapters.sms.port import SmsDeliveryError, SmsSender

__all__ = [
    "MockSmsSender",
    "SentSms",
    "SmsDeliveryError",
    "SmsSender",
]
