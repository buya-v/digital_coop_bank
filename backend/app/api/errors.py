"""API error foundation — the uniform error envelope (04 §3.0 / root.yaml `Error`).

Any feature raises `ApiError(status_code, code, message, details?)`; the
registered handler renders the exact envelope the OpenAPI `Error` schema pins:
`{"error": {"code", "message", "correlation_id", "details"?}}`
(`additionalProperties: false`). EP-1 is the first feature and establishes this
pattern so later routers reuse one error shape rather than each inventing its own.

Only explicit `ApiError`s are wrapped here; FastAPI's own request-validation
422 keeps its framework default shape, so field-shape validation this slice must
surface uniformly (e.g. registration_number) is raised as an `ApiError` from the
service/router, not left to pydantic.
"""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class ApiError(Exception):
    """A domain error carrying the HTTP status and the canonical `code`.

    `correlation_id` is minted per response by the handler. Reading it from an
    inbound tracing header is a later concern (documented, not assumed).
    """

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: Optional[list[object]] = None,  # noqa: UP045
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details


async def api_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Render an `ApiError` as the pinned `Error` envelope."""
    assert isinstance(exc, ApiError)  # registered only for ApiError
    error: dict[str, object] = {
        "code": exc.code,
        "message": exc.message,
        "correlation_id": str(uuid.uuid4()),
    }
    if exc.details is not None:
        error["details"] = exc.details
    return JSONResponse(status_code=exc.status_code, content={"error": error})


def register_error_handlers(app: FastAPI) -> None:
    """Wire the uniform error envelope onto the application."""
    app.add_exception_handler(ApiError, api_error_handler)
