# wazo-docker

## **WARNING**: Everything in this repo is experimental and not ready for the production

Contains docker-compose file to setup wazo-platform project.

The main goal of this repository is to list and document what we need to have
container ready services. In other word, when this repository will contains only
a docker-compose without hacks (volumes, custom images, etc..), then we will
have container ready services

## Prerequisite

- Install docker
- Clone the following repositories
  - wazo-platform/wazo-auth-keys
  - wazo-platform/xivo-config

- set environment variable `LOCAL_GIT_REPOS=<path/to/cloned/repositories>`

## Prepare Environment

- `for repo in wazo-auth-keys xivo-config; do git -C "$LOCAL_GIT_REPOS/$repo" pull; done`
- `docker compose pull --ignore-pull-failures`
  - Note: A lot of images won't be found on registry since they are built locally

- `docker compose build --pull --no-cache`

### Use Development Branch Environment

If you want to use a feature in development. You can override docker image from
a local folder with the following steps:

- `cd /<path>/<to>/wazo-<service>/`
- `docker build -t wazoplatform/wazo-<service>:latest .`
- `cd /<path>/<to>/wazo-docker/`
- `docker compose build <service> --no-cache`
- `docker compose up -d`

> **Where `<service>` can be**: `asterisk`, `bootstrap`, `chatd`, `confd`,
> `dird`, `provd`, `webhookd`, `websocketd`, `auth`, `deployd`

## Start Environment

- `docker compose up --detach`
- Need to accept custom certificate on `https://localhost:8443`
- default username / password: `root` / `secret`

## Clean Environment

- `docker compose down --volumes`
- `docker compose up --detach`

## Restart Environment

- `docker compose down`
- `docker compose up --detach`

## Test Environment

- Install `curl` and `jq` commands
- `./verify.sh`

## Troubleshooting

- A good starting point for debugging is the `bootstrap` container log
- To get sql prompt: `docker compose exec postgres psql -U asterisk wazo`
- To use wazo-auth-cli: `docker compose run --entrypoint bash bootstrap`
- To update only one service without restarting everything

  ```bash
  docker compose stop webhookd
  docker compose rm webhookd
  docker compose up webhookd
  ```

- **Avoid to use `docker compose restart <service>`**. It will only restart
  container without new parameters (mount, config, variable)
- When running softphone on the same host than docker, don't use 127.0.0.1:5060,
  but use *public* IP (i.e. 192.168.x.x:5060)
- asterisk configuration are not reload automatically. You must:

  ```bash
  docker compose exec asterisk bash
  wazo-confgen asterisk/pjsip.conf --invalidate
  asterisk -rx 'core reload'
  ```

## Security

This project has not been developed to be used on production nor exposed on
internet. Here is a non-exhaustive list of security concerns that has been found
during development:

- wazo-phoned expose all unsecured endpoints through nginx
- nginx configuration can be updated on upstream and be desynchronized with this
  configuration
- Container images embed the `netcat` tool that can be used to open a remote
  shell.
- Credentials are hardcoded

---

## db-migrator (one-shot migrations)

This repository includes a `db-migrator` helper image under `docker/db-migrator`.
Its role is to run database initialization and Alembic migrations for the
local repositories mounted under `./repos` before starting services that rely
on the database schema.

How it works (short):
- Mounts `./repos` into the container at `/home/ubuntu`.
- Waits for Postgres to be reachable.
- Runs `xivo_dao.init_db()` to ensure core DAO tables.
- Discovers `alembic.ini` files under `/home/ubuntu` and, for each repo:
  - Creates a temporary venv, installs the repo's `requirements.txt` (or
    installs `alembic`), sets `PYTHONPATH` to the repo root and runs
    `alembic -c <cfg> upgrade head` from the repo root.

Run it manually:

```bash
docker compose -f docker-compose.yml up -d --no-deps --force-recreate --build db-migrator
docker compose -f docker-compose.yml logs --no-log-prefix --tail=400 db-migrator
```

Per-repo logs are written to `migrator_logs/` under the working directory of
the migrator process (this directory is created by the migrator when it runs).

If a repo's migrations fail, inspect `migrator_logs/<repo>.log` for details.

Note about runtime images and virtualenvs
----------------------------------------

Some service Dockerfiles build and copy a virtualenv from a build stage
into the runtime stage (for example `/opt/venv`). That virtualenv contains
the installed Python interpreter and console entrypoints (the `wazo-*`
executables). If the runtime image does not include a compatible Python
base (for example when using `debian:11-slim`), the copied virtualenv's
binaries won't run: you'll see errors like "/opt/venv/bin/wazo-call-logd:
no such file or directory". To preserve a working virtualenv you must either:

- use a runtime base that provides the same Python ABI (e.g. `python:3.9-slim`),
  or
- avoid copying a venv and instead install the package into the runtime
  system Python (pip install into the image).

We chose to make runtime images keep Python (via `python:<version>` base)
because it keeps the multi-stage build fast and reproduces the upstream
packaging assumptions.

