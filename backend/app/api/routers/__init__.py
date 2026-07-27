"""API routers — FastAPI feature routes (thin HTTP adapters).

A router validates I/O against the OpenAPI contract (via pydantic models),
delegates to a service, and maps domain errors to the uniform error envelope
(`app.api.errors`). It owns the request transaction boundary (commit on a
successful mutation). EP-1 onboarding is the first feature router.
"""
