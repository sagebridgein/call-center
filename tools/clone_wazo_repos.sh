#!/usr/bin/env bash
# Clone a list of wazo-platform repositories into ./repos
# Usage: ./tools/clone_wazo_repos.sh [destination-dir]
set -euo pipefail
DEST=${1:-./repos}
mkdir -p "$DEST"
cd "$DEST"
# List of repos to clone. Add or remove names as needed.
REPOS=(
  wazo-dird
  wazo-confd
  wazo-auth
  wazo-auth-cli
  wazo-provd
  wazo-websocketd
  wazo-webhookd
  wazo-call-logd
  # add other repo names you need migrations for
)
ORG=${WAZO_ORG:-wazo-platform}
GIT_BASE="https://github.com/${ORG}"
for r in "${REPOS[@]}"; do
  if [ -d "$r" ]; then
    echo "Updating $r"
    (cd "$r" && git pull --ff-only)
  else
    echo "Cloning $r"
    git clone "${GIT_BASE}/${r}.git"
  fi
done

echo "Cloned/updated repos into $(pwd)"
