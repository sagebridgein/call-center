#!/usr/bin/env bash
set -euo pipefail

# Normalize malformed transport lines in Asterisk pjsip config files inside the
# running asterisk container, reload PJSIP, and print status/logs.

DOCKER_CMD=docker

if ! command -v "$DOCKER_CMD" >/dev/null 2>&1; then
  echo "docker not found in PATH"
  exit 1
fi

# find asterisk container
CID=$($DOCKER_CMD ps --filter "name=asterisk" --format '{{.ID}}' | head -n1 || true)
if [ -z "$CID" ]; then
  echo "No running container with name containing 'asterisk' found."
  echo "Run 'docker ps' to inspect containers."
  exit 1
fi

echo "Found asterisk container: $CID"
echo "Normalizing transport lines in /etc/asterisk and /etc/asterisk/pjsip.d/*.conf ..."

# safe in-container edits: collapse repeated -local and replace bare transport-udp
$DOCKER_CMD exec "$CID" bash -lc '
set -e
FILES=(/etc/asterisk/pjsip.d/*.conf /etc/asterisk/pjsip.conf)
for f in "${FILES[@]}"; do
  [ -f "$f" ] || continue
  echo "---- BEFORE: $f (first 12 lines) ----"
  sed -n "1,12p" "$f" || true
  perl -0777 -pi -e "s/^transport=transport-udp(?:-local)*/transport=transport-udp-local/mg" "$f" || true
  echo "---- AFTER:  $f (first 12 lines) ----"
  sed -n "1,12p" "$f" || true
done

echo "Reloading PJSIP and listing objects..."
asterisk -rx "pjsip reload" || true
asterisk -rx "pjsip list endpoints" || true
asterisk -rx "pjsip list aors" || true
asterisk -rx "pjsip list auths" || true
echo "---- tail /var/log/asterisk/messages ----"
tail -n 200 /var/log/asterisk/messages || true
'

echo "Done. If problems remain, paste the above output here."
#!/usr/bin/env bash
set -euo pipefail

# Try using sudo if available and not root
DOCKER_CMD="docker"
if ! command -v docker >/dev/null 2>&1; then
  echo "docker not found in PATH"
  exit 1
fi

# locate asterisk container (matching name contains 'asterisk')
CID=$($DOCKER_CMD ps --filter "name=asterisk" --format '{{.ID}}' | head -n1 || true)
if [ -z "$CID" ]; then
  echo "No running container with name containing 'asterisk' found."
  echo "Run 'docker ps' to inspect containers."
  exit 1
fi

echo "Found asterisk container: $CID"
echo "Normalizing transport lines in /etc/asterisk and /etc/asterisk/pjsip.d/*.conf ..."

# Perform safe in-container edits: collapse repeated -local and replace bare transport-udp
$DOCKER_CMD exec "$CID" bash -lc '
set -e
FILES=(/etc/asterisk/pjsip.d/*.conf /etc/asterisk/pjsip.conf)
for f in "${FILES[@]}"; do
  [ -f "$f" ] || continue
  # show head for operator info
  echo "---- BEFORE: $f ----"
  sed -n "1,6p" "$f" || true
  # normalize repeated "-local" and bare transport-udp lines
  perl -0777 -pi -e "s/^transport=transport-udp(?:-local)*/transport=transport-udp-local/mg" "$f" || true
  echo "---- AFTER: $f (first 6 lines) ----"
  sed -n "1,6p" "$f" || true
done

echo "Reloading PJSIP and listing objects..."
asterisk -rx "pjsip reload" || true
asterisk -rx "pjsip list endpoints" || true
asterisk -rx "pjsip list aors" || true
asterisk -rx "pjsip list auths" || true
echo "---- tail /var/log/asterisk/messages ----"
tail -n 200 /var/log/asterisk/messages || true
'

echo "Done. If problems remain, inspect the logs above and the files under /etc/asterisk inside the container."
