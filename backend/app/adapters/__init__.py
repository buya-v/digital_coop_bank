"""External-integration adapters (ports + implementations).

Each subpackage is a PORT (an interface the app depends on) plus one or more
implementations. This slice adds `ekyc` — the ХУР/XYP state-register KYC lookup
behind an interface with a deterministic in-memory mock. The concrete provider is
a procurement decision (TBD, CLAUDE.md blocking question #2); the app depends only
on the port, never on a vendor SDK.
"""
