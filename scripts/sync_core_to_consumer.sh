#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  scripts/sync_core_to_consumer.sh --target /path/to/consumer [--apply]

Synchronize tracked files from the current LaPythie checkout into a consumer
project checkout.
The script does not fetch or checkout branches. Run it from the LaPythie
branch you want to deploy.

By default, the script runs as a dry run. Pass --apply to copy files.
Consumer-local configuration is intentionally excluded.
USAGE
}

TARGET_DIR=""
APPLY=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target)
      TARGET_DIR="${2:-}"
      shift 2
      ;;
    --apply)
      APPLY=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "ERROR: unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ -z "$TARGET_DIR" ]]; then
  echo "ERROR: --target is required" >&2
  usage >&2
  exit 1
fi

SOURCE_DIR="$(git rev-parse --show-toplevel)"
TARGET_DIR="$(cd "$TARGET_DIR" && pwd)"

if [[ "$SOURCE_DIR" == "$TARGET_DIR" ]]; then
  echo "ERROR: target must be different from the LaPythie source checkout" >&2
  exit 1
fi

if [[ ! -d "$TARGET_DIR/.git" ]]; then
  echo "ERROR: target must be a git worktree: $TARGET_DIR" >&2
  exit 1
fi

if ! command -v rsync >/dev/null 2>&1; then
  echo "ERROR: rsync is required" >&2
  exit 1
fi

mode_args=(-ain)
if [[ "$APPLY" == "1" ]]; then
  mode_args=(-ai)
fi

echo "Source: $SOURCE_DIR"
echo "Target: $TARGET_DIR"
if [[ "$APPLY" == "1" ]]; then
  echo "Mode: apply"
else
  echo "Mode: dry-run"
fi

rsync "${mode_args[@]}" \
  --from0 \
  --files-from=<(cd "$SOURCE_DIR" && git ls-files -z) \
  --exclude='.git/' \
  --exclude='.env' \
  --include='.env.example' \
  --exclude='.env.*' \
  --exclude='apps/api/config/local/' \
  --exclude='apps/api/config/project.yaml' \
  --exclude='apps/api/config/metadata_registry.project.yaml' \
  --exclude='artifacts/' \
  --exclude='data/' \
  --exclude='storage/' \
  --exclude='postgres_data/' \
  --exclude='qdrant_data/' \
  --exclude='node_modules/' \
  --exclude='.venv/' \
  --exclude='.pytest_cache/' \
  --exclude='.ruff_cache/' \
  "$SOURCE_DIR/" "$TARGET_DIR/"
