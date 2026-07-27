"""Service layer — feature business logic, sitting between routers and repositories.

A service owns the rules for one feature: validation, status transitions, and
orchestration across repositories. Routers stay thin (HTTP in/out, error
mapping); repositories stay dumb (row access). EP-1 onboarding is the first
feature and sets this pattern.
"""
