"""eKYC provider port + implementations (ХУР/XYP state-register lookup).

The onboarding KYC step is a STATE-REGISTER lookup, NOT biometric face-match
(CLAUDE.md blocking question #2, PO provisional direction; DEC-5). The concrete
provider is a procurement decision (TBD), so the app depends on `EkycProvider`
(the port) and this slice ships `MockEkycProvider` (a deterministic, no-network
stub). Swapping in a real ХУР/XYP client is a new implementation of the same
port, not a change to the onboarding service.
"""
from app.adapters.ekyc.mock import MockEkycProvider
from app.adapters.ekyc.port import (
    EkycApplicant,
    EkycProvider,
    EkycProviderError,
    EkycResult,
    EkycSession,
)

__all__ = [
    "EkycApplicant",
    "EkycProvider",
    "EkycProviderError",
    "EkycResult",
    "EkycSession",
    "MockEkycProvider",
]
