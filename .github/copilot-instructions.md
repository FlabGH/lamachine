# Copilot Instructions for LaPythie

## Repository Scope

LaPythie is a generic documentary AI core. The repository is organised around:

- `apps/` — backend application services.
- `corpus/` — neutral sample data for ingestion and retrieval checks.
- `infra/` — infrastructure configuration for Docker, Postgres, Qdrant and Caddy.
- `scripts/` — operational scripts.
- `.env.example` — environment template; copy to `.env` locally and never commit secrets.

Remote: `origin`, default branch `main`.

## Contribution Conventions

- Use a feature or fix branch for application changes.
- Keep commits scoped to one functional intent.
- Prefer small, testable changes.
- Do not commit local secrets, generated artifacts or private data.

## Generated Outputs

Generated outputs should stay out of tracked source unless they are intentionally added as tests, examples or documentation.

## Project Notes

- The core must remain generic and reusable by consuming projects.
- Project-specific values belong in consuming repositories or neutral examples, not in core mechanisms.
- Infrastructure and runtime names should use LaPythie naming.
