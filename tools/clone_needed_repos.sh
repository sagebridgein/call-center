#!/usr/bin/env bash
# Clone only the repositories referenced by build contexts in docker-compose.yml
# Usage: ./tools/clone_needed_repos.sh [dest_dir] [org]
set -euo pipefail
DEST=${1:-./repos}
ORG=${2:-${WAZO_ORG:-wazo-platform}}
COMPOSE_FILE=${3:-./docker-compose.yml}

if [ ! -f "$COMPOSE_FILE" ]; then
  echo "docker-compose.yml not found at $COMPOSE_FILE"
  exit 1
fi
mkdir -p "$DEST"
cd "$DEST"

# Extract context paths like: context: /home/ubuntu/wazo-dird
# then strip prefix and get repo name
REPOS=$(grep -E "context:\s*/home/ubuntu/[a-zA-Z0-9_-]+" "$COMPOSE_FILE" | sed -E 's/.*context:\s*\/home\/ubuntu\///' | tr -d '\r' | sort -u)

if [ -z "$REPOS" ]; then
  echo "No /home/ubuntu/* build contexts found in $COMPOSE_FILE"
  exit 0
fi

GIT_BASE="https://github.com/${ORG}"
for r in $REPOS; do
  if [ -d "$r" ]; then
    echo "Updating $r"
    (cd "$r" && git fetch --all && git pull --ff-only) || echo "Failed to update $r"
  else
    echo "Cloning $r"
    git clone "${GIT_BASE}/${r}.git" "$r" || echo "Failed to clone $r"
  fi
done

echo "Cloned/updated the following repos:"
printf '%s
' $REPOS
