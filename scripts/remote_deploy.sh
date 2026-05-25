#!/usr/bin/env bash
set -euo pipefail

# Remote deployment helper for LaMachine POC.
# Usage:
#   REMOTE_HOST=151.115.151.104 REMOTE_USER=ubuntu REMOTE_DIR=/opt/lamachine/data/lamachinepoc ./scripts/remote_deploy.sh
# Optionally set REMOTE_BRANCH (default current branch) and REMOTE_DOCKER_COMPOSE_FILES
# (default "infra/compose/docker-compose.yml infra/compose/docker-compose.prod.yml").

REMOTE_HOST=${REMOTE_HOST:-}
REMOTE_USER=${REMOTE_USER:-ubuntu}
REMOTE_DIR=${REMOTE_DIR:-}
REMOTE_BRANCH=${REMOTE_BRANCH:-}
REMOTE_DOCKER_COMPOSE_FILES=${REMOTE_DOCKER_COMPOSE_FILES:-"infra/compose/docker-compose.yml infra/compose/docker-compose.prod.yml"}

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

RSYNC_EXCLUDES=(
  .git
  .venv
  node_modules
  dist
  build
  data
  storage
  postgres_data
  qdrant_data
  .DS_Store
  .pytest_cache
  .ruff_cache
  .env
  '*.log'
  '*.pem'
  '*.key'
  'id_*'
  '*.pub'
)

echo "Deploying branch '$LOCAL_BRANCH' to $REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR"
echo "Using remote Docker Compose files: $REMOTE_DOCKER_COMPOSE_FILES"

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

echo "3) Updating remote repository and restarting Docker Compose"
if ssh -o BatchMode=yes "$REMOTE_USER@$REMOTE_HOST" bash -e <<REMOTE
  set -euo pipefail
  cd "$REMOTE_DIR"
  git fetch --all --prune
  git checkout "$REMOTE_BRANCH"
  git reset --hard "origin/$REMOTE_BRANCH"
REMOTE
then
  echo "Remote git update succeeded"
else
  echo "Remote git update failed; falling back to rsync-based deploy"
  rsync -av --delete "${RSYNC_EXCLUDES[@]/#/--exclude=}" ./ "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/"
fi

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

echo "4) Verifying remote API health"
ssh -o BatchMode=yes "$REMOTE_USER@$REMOTE_HOST" bash -e <<REMOTE
  set -euo pipefail
  cd "$REMOTE_DIR"
  compose_args=()
  for compose_file in $REMOTE_DOCKER_COMPOSE_FILES; do
    compose_args+=("-f" "\$compose_file")
  done
  for i in 1 2 3 4 5; do
    if docker compose "\${compose_args[@]}" exec -T api sh -c 'python -c "import urllib.request, json; print(urllib.request.urlopen(\"http://127.0.0.1:8000/health\").read().decode())"' ; then
      exit 0
    fi
    echo "API health check attempt \$i failed, retrying..."
    sleep 2
  done
  echo "ERROR: remote API health check failed after retries"
  exit 1
REMOTE

echo "Deployment complete. If you need to enable Mistral provider, update the remote .env file and re-run this script."
