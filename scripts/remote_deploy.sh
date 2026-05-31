#!/usr/bin/env bash
set -euo pipefail

# Remote deployment helper for LaMachine POC.
# Usage:
#   REMOTE_HOST=151.115.151.104 REMOTE_USER=ubuntu REMOTE_DIR=/opt/lamachine/data/lamachinepoc ./scripts/remote_deploy.sh
# Optionally set REMOTE_BRANCH (default current branch) and REMOTE_DOCKER_COMPOSE_FILES
# (default "infra/compose/docker-compose.yml infra/compose/docker-compose.prod.yml").
# Optional deployment checks:
#   REMOTE_REBUILD_DB=1 rebuilds the remote database from versioned SQL files.
#   REMOTE_APPLY_FIXTURE=1 loads apps/api/app/db/fixtures/phase3_step1_fixture.sql after rebuild.
#   REMOTE_RUN_AUDIT=1 runs apps/api/app/db/queries/audit_documentary_metadata.sql after deploy.

REMOTE_HOST=${REMOTE_HOST:-}
REMOTE_USER=${REMOTE_USER:-ubuntu}
REMOTE_DIR=${REMOTE_DIR:-}
REMOTE_BRANCH=${REMOTE_BRANCH:-}
REMOTE_DOCKER_COMPOSE_FILES=${REMOTE_DOCKER_COMPOSE_FILES:-"infra/compose/docker-compose.yml infra/compose/docker-compose.prod.yml"}
REMOTE_REBUILD_DB=${REMOTE_REBUILD_DB:-0}
REMOTE_APPLY_FIXTURE=${REMOTE_APPLY_FIXTURE:-0}
REMOTE_RUN_AUDIT=${REMOTE_RUN_AUDIT:-1}

if [[ -z "$REMOTE_HOST" ]]; then
  echo "ERROR: REMOTE_HOST must be set"
  exit 1
fi

if [[ -z "$REMOTE_DIR" ]]; then
  echo "ERROR: REMOTE_DIR must be set"
  exit 1
fi

LOCAL_BRANCH=$(git rev-parse --abbrev-ref HEAD)
REMOTE_BRANCH=${REMOTE_BRANCH:-$LOCAL_BRANCH}

echo "Deploying branch '$LOCAL_BRANCH' to $REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR"
echo "Using remote Docker Compose files: $REMOTE_DOCKER_COMPOSE_FILES"
echo "Remote rebuild DB: $REMOTE_REBUILD_DB"
echo "Remote apply fixture: $REMOTE_APPLY_FIXTURE"
echo "Remote run audit: $REMOTE_RUN_AUDIT"

echo "1) Verifying local git status"
git status --short

if [[ -n "$(git status --short)" ]]; then
  echo "ERROR: local working tree is dirty. Commit or stash changes before deploying."
  exit 1
fi

if ! git rev-parse --verify "$REMOTE_BRANCH" >/dev/null 2>&1; then
  echo "ERROR: branch '$REMOTE_BRANCH' does not exist locally"
  exit 1
fi

# Push branch if it has a tracking remote.
if git rev-parse --abbrev-ref --symbolic-full-name @{u} >/dev/null 2>&1; then
  echo "2) Pushing local branch to upstream"
  git push
else
  echo "2) No upstream tracking branch configured for '$REMOTE_BRANCH', skipping git push"
fi

echo "3) Updating remote repository from Git"
ssh -o BatchMode=yes "$REMOTE_USER@$REMOTE_HOST" bash -e <<REMOTE
  set -euo pipefail
  cd "$REMOTE_DIR"
  git fetch --all --prune
  git checkout "$REMOTE_BRANCH"
  git reset --hard "origin/$REMOTE_BRANCH"
REMOTE
echo "Remote git update succeeded"

echo "4) Rebuilding and restarting remote Docker Compose"
ssh -o BatchMode=yes "$REMOTE_USER@$REMOTE_HOST" bash -e <<REMOTE
  set -euo pipefail
  cd "$REMOTE_DIR"
  compose_args=()
  for compose_file in $REMOTE_DOCKER_COMPOSE_FILES; do
    compose_args+=("-f" "\$compose_file")
  done
  docker compose "\${compose_args[@]}" pull
  docker compose "\${compose_args[@]}" up -d --build
  docker compose "\${compose_args[@]}" ps
REMOTE

if [[ "$REMOTE_REBUILD_DB" == "1" ]]; then
  echo "5) Rebuilding remote database from versioned SQL"
  ssh -o BatchMode=yes "$REMOTE_USER@$REMOTE_HOST" bash -e <<REMOTE
    set -euo pipefail
    cd "$REMOTE_DIR"
    compose_args=()
    for compose_file in $REMOTE_DOCKER_COMPOSE_FILES; do
      compose_args+=("-f" "\$compose_file")
    done
    db_user=\$(docker compose "\${compose_args[@]}" exec -T postgres printenv POSTGRES_USER)
    db_name=\$(docker compose "\${compose_args[@]}" exec -T postgres printenv POSTGRES_DB)
    docker compose "\${compose_args[@]}" exec -T postgres psql -v ON_ERROR_STOP=1 -U "\$db_user" -d postgres -c "DROP DATABASE IF EXISTS \"\$db_name\" WITH (FORCE);" -c "CREATE DATABASE \"\$db_name\" OWNER \"\$db_user\";"
    docker compose "\${compose_args[@]}" exec -T postgres psql -v ON_ERROR_STOP=1 -U "\$db_user" -d "\$db_name" < apps/api/app/db/migrations/001_documentary_schema.sql
    docker compose "\${compose_args[@]}" exec -T postgres psql -v ON_ERROR_STOP=1 -U "\$db_user" -d "\$db_name" < apps/api/app/db/migrations/002_documentary_metadata_contract.sql
REMOTE
else
  echo "5) Skipping remote database rebuild"
fi

if [[ "$REMOTE_APPLY_FIXTURE" == "1" ]]; then
  echo "6) Loading remote Phase 3 fixture"
  ssh -o BatchMode=yes "$REMOTE_USER@$REMOTE_HOST" bash -e <<REMOTE
    set -euo pipefail
    cd "$REMOTE_DIR"
    compose_args=()
    for compose_file in $REMOTE_DOCKER_COMPOSE_FILES; do
      compose_args+=("-f" "\$compose_file")
    done
    db_user=\$(docker compose "\${compose_args[@]}" exec -T postgres printenv POSTGRES_USER)
    db_name=\$(docker compose "\${compose_args[@]}" exec -T postgres printenv POSTGRES_DB)
    docker compose "\${compose_args[@]}" exec -T postgres psql -v ON_ERROR_STOP=1 -U "\$db_user" -d "\$db_name" < apps/api/app/db/fixtures/phase3_step1_fixture.sql
REMOTE
else
  echo "6) Skipping remote fixture load"
fi

echo "7) Verifying remote API health"
ssh -o BatchMode=yes "$REMOTE_USER@$REMOTE_HOST" bash -e <<REMOTE
  set -euo pipefail
  cd "$REMOTE_DIR"
  compose_args=()
  for compose_file in $REMOTE_DOCKER_COMPOSE_FILES; do
    compose_args+=("-f" "\$compose_file")
  done
  for i in 1 2 3 4 5 6 7 8 9 10; do
    if docker compose "\${compose_args[@]}" exec -T api sh -c 'python -c "import urllib.request, json; print(urllib.request.urlopen(\"http://127.0.0.1:8000/health\").read().decode())"' ; then
      exit 0
    fi
    echo "API health check attempt \$i failed, retrying..."
    sleep 2
  done
  echo "ERROR: remote API health check failed after retries"
  exit 1
REMOTE

if [[ "$REMOTE_RUN_AUDIT" == "1" ]]; then
  echo "8) Running remote documentary metadata audit"
  ssh -o BatchMode=yes "$REMOTE_USER@$REMOTE_HOST" bash -e <<REMOTE
    set -euo pipefail
    cd "$REMOTE_DIR"
    compose_args=()
    for compose_file in $REMOTE_DOCKER_COMPOSE_FILES; do
      compose_args+=("-f" "\$compose_file")
    done
    db_user=\$(docker compose "\${compose_args[@]}" exec -T postgres printenv POSTGRES_USER)
    db_name=\$(docker compose "\${compose_args[@]}" exec -T postgres printenv POSTGRES_DB)
    docker compose "\${compose_args[@]}" exec -T postgres psql -v ON_ERROR_STOP=1 -U "\$db_user" -d "\$db_name" < apps/api/app/db/queries/audit_documentary_metadata.sql
REMOTE
else
  echo "8) Skipping remote documentary metadata audit"
fi

echo "Deployment complete. If you need to enable Mistral provider, update the remote .env file and re-run this script."
