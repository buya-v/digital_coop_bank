"""Repository layer — the persistence-access pattern for every feature.

A repository wraps a SQLAlchemy `Session` and exposes intention-revealing data
access for one aggregate, keeping raw ORM/session calls out of the service and
router layers. EP-1 onboarding is the first feature; the shape established here
(`BaseRepository` + a per-aggregate repository) is the pattern later features
follow. No business logic and no transaction control live here — services own
rules, and the request-scoped session (`app.api.deps.get_session`) owns commit.
"""
