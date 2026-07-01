# Project Agent Instructions

## Mandatory Local Skill Loading

Before modifying backend code in this repository, the agent must read the following files in order:

1. `.local-skills/ai-short-drama-dev/SKILL.md`
2. `.local-skills/backend-fastapi-dev/SKILL.md`
3. `docs/technical/coding-standards.md`

This applies to any change under `apps/api`, including FastAPI routes, Pydantic schemas, service logic, SQLAlchemy models, Alembic migrations, backend validation, error handling, and model API integration.

## Backend Comment Requirements

When generating or modifying backend code, add concise Chinese comments for non-obvious logic and project-specific rules, especially:

- Business rules and product constraints.
- Cross-field validation.
- Security and privacy boundaries.
- State transitions and overwrite protection.
- AI generation context priority rules.
- Database version fields, status fields, historical retention rules, relationships, and migration compatibility logic.

Avoid comments that only restate syntax, variable names, function names, or obvious control flow. Comments should explain why a rule exists, what boundary it protects, or what future maintainers must not accidentally break.

## Required Final Self-check

Before finishing any backend code change, the agent must self-check whether the modified code is missing required Chinese comments for key logic.

The final response must explicitly mention that this backend comment self-check was completed.
