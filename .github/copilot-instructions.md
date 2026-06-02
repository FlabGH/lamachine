# Copilot Instructions for CLI_papillon

> Generated from the [CLI_Template](https://github.com/Marcoxito68/CLI_Template) repository.
> Local working copy of the upstream repository [FlabGH/lamachinepoc](https://github.com/FlabGH/lamachinepoc).

## Repository scope

Reference working directory for this project: `D:\github\CLI_papillon`.

Local clone of `FlabGH/lamachinepoc` (POC "la machine"). The repo is **not vierge** and already contains application code organised as:

- `apps/` — application services (frontend, backend, etc.)
- `corpus/` — data / ingestion corpus (see `corpus/poc_ia/files/`)
- `infra/` — infrastructure (Docker, Postgres, Qdrant, …)
- `scripts/` — operational scripts
- `Makefile` — entry points for build/run/dev tasks
- `.env.example` — env template; copy to `.env` locally (never commit)

Remote: `origin = https://github.com/FlabGH/lamachinepoc.git` (public, default branch `main`).

## Permissions and approval-free setup

This workstation is configured to minimise approval prompts so that explicit user requests run end-to-end without interruption.

- **`--yolo` is enabled by default**: the PS7 profile (`D:\OneDrive\Documents\PowerShell\profile.ps1`) wraps `copilot` to add `--yolo` automatically. This auto-approves tool, path and URL prompts for the session.
- **If you launched Copilot without `--yolo`** (e.g. from another shell): run `/allow-all` once at the start of the session to enable all permissions (tools, paths, URLs).
- **Per-directory access**: `/add-dir <path>` adds a directory to the allowed list; `/list-dirs` displays them. The filesystem MCP server is already scoped to `D:\github` globally.
- **Reset**: `/reset-allowed-tools` if you ever need to revoke and start fresh.
- **MCP servers** preconfigured globally in `C:\Users\marc\.copilot\mcp-config.json`:
  - `playwright` — browser automation
  - `filesystem` — access scoped to `D:\github`
  - `memory` — per-project knowledge graph stored in `.copilot-memory.json` at the cwd (ignored by global gitignore)
  - `fetch` (`mcp-server-fetch` via `uvx`) — retrieve URLs / web content
- **Practical implication**: launch Copilot from this repo root to inherit the expected MCP setup and per-project memory; do not re-confirm permissions in normal use.

## Output conventions

- **All generated outputs (decks, documents, exports, artifacts) must be written to the `OUTPUT/` folder at the repo root.**
- If `OUTPUT/` does not exist, create it before writing.
- Do not write generated outputs elsewhere in the repo (e.g., not in `docs/`, `corpus/`, or the repo root).

## Presentation conventions

- **Primary audience**: decks are mostly customer-facing.
- **Required narrative flow**: `Context -> Problem -> Solutions and examples -> Next steps`.
- **Two slide archetypes are expected**:
  - **Executive slide**: limited bullets, concise messaging, and a high-quality/appropriate illustration.
  - **Data-driven slide**: detailed description and explanation of the data and implications.
- **Evidence standard**: every major claim must include a source, or be explicitly labeled **Assumption**.
- **Language standard**: keep wording concise and executive-ready.
- **No inference policy**: when data is missing, use `Not specified`.

## Contribution conventions

- This repo is **shared with other contributors** on `FlabGH/lamachinepoc` — be conservative on `main`.
- Branch naming:
  - `feature/<short-description>`
  - `fix/<short-description>`
  - `chore/<short-description>`
- Commit prefixes in use: `feat:`, `fix:`, `docs:`, `chore:`
- PR descriptions should cover: **What**, **Why**, **How to test**, **Risks/Impact**
- Prefer PRs over direct pushes to `main` when touching application code under `apps/` or `infra/`.

## Project-specific notes

<!--
Add anything specific to this project below:
- domain knowledge (la machine POC)
- naming conventions
- external services / APIs (Postgres, Qdrant, …)
- people to consult (FlabGH)
- known pitfalls (e.g. case-sensitive collision on `apps/frontend/Dockerfile` vs `DockerFile` when cloning on Windows)
-->

- **Known pitfall (Windows)**: clone warns about case-collision on `apps/frontend/Dockerfile` / `DockerFile`. Only one is materialised in the working tree on NTFS case-insensitive volumes. Do not "fix" this locally — coordinate upstream.
- **Secrets**: `.env`, `.env.*` (except `.env.example`), `*.pem`, `*.key`, `id_*`, `*.pub` are gitignored. Never commit them.

## Interaction style

- **Quand l'intention est explicite, exécute directement.** Ne pose pas de questions de confirmation pour des choix déjà implicites dans la demande ou couverts par les conventions par défaut du repo.
- N'utilise `ask_user` que pour les ambiguïtés qui bloquent réellement le résultat (scope, comportement, choix où plusieurs options valides existent sans défaut évident).
- **N'introduis pas non plus de pauses de validation textuelles** ("dois-je continuer ?", "veux-tu que je commite ?", "tu confirmes ?") quand l'utilisateur a déjà demandé l'action complète : poursuis jusqu'au résultat livré.
- **Défauts implicites pour ce workstation, à appliquer sans demander** :
  - Création de repo GitHub via `gh` (CLI déjà authentifié).
  - Visibilité **privée** par défaut (mais ici `origin` est déjà **public** — ne pas tenter de changer la visibilité sans demande explicite).
  - Branche `main` par défaut.
  - Commits avec le préfixe approprié (`feat:`, `fix:`, `docs:`, `chore:`) et trailer `Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>`.
  - Push automatique sur `origin` après commit quand le repo a déjà un remote — **sauf** sur `main` de ce repo partagé : préférer une branche dédiée + PR pour les changements applicatifs non triviaux.
- **N'attends pas non plus d'approbation pour** : lectures de fichiers, recherches, builds/tests/lints d'un repo, écritures dans le repo courant, et commandes shell équivalentes à celles déjà acceptées dans la session.
- Si une commande est destructrice et non triviale (suppression massive, force-push, rewrite d'historique), avertis explicitement avant — c'est la seule catégorie où une confirmation reste légitime.
