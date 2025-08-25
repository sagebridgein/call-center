# wazo-auth-keys [![Build Status](https://jenkins.wazo.community/buildStatus/icon?job=wazo-auth-keys)](https://jenkins.wazo.community/job/wazo-auth-keys)

A small tool to automatically provision/configure service keys in Wazo.

## Pre-requisite

Configuration to connect to the wazo-auth daemon are fetched from the `wazo-auth-cli`
configuration. It is possible to specify the wazo-auth-cli configuration directory with the
`--wazo-auth-cli-config` option or with the environment variable `WAZO_AUTH_CLI_CONFIG`. See the
[wazo-auth-cli documentation](https://github.com/wazo-platform/wazo-auth-cli) for more information.


## Configuration

Configuration file is at the following location:

```
/etc/wazo-auth-keys/config.yml
```

The `/etc/wazo-auth-keys/config.yml` is the default configuration file shipped with the debian
package. This file should not be modified but can be used as a reference.

```sh
wazo-auth-keys --config ~/.config/wazo-auth-keys/config.yml
```


## Commands

### Completion

```sh
wazo-auth-keys complete > /etc/bash_completion.d/wazo-auth-keys
```

### Services

Updating services

```sh
wazo-auth-keys service update
```

Cleaning service

```sh
wazo-auth-keys service clean
```


## Default provisioning / sample config

A sample default provisioning file has been added to the repository to help bootstrap softphone users, devices, lines and a Twilio SIP trunk:

Path: ./wazo-auth-keys/etc/wazo-auth-keys/config.yml

This file contains example users (softphone auth), device entries, line numbers and a "twilio" SIP trunk section. Replace placeholders (username/password, Twilio Account SID / Auth Token / phone numbers) with your real values before deploying.

Example docker-compose snippet to bind the file into the container so bootstrap tools can read it.
Make sure to mount the same file into your auth and bootstrap (or provisioning) containers so the service sees the desired users/trunks.

```yaml
# bind the repository config into the container so bootstrap tools and auth can read it
services:
  auth:
    image: ajaysehwal81/wazo-auth
    volumes:
      - ./wazo-auth-keys/etc/wazo-auth-keys/config.yml:/etc/wazo-auth-keys/config.yml:ro
      # keep any existing mounts you need
  bootstrap:
    image: your-bootstrap-image
    volumes:
      - ./wazo-auth-keys/etc/wazo-auth-keys/config.yml:/etc/wazo-auth-keys/config.yml:ro
      - ./wazo-auth-keys:/var/lib/wazo-auth-keys:rw
```

Notes:
- If you mount the single file as /etc/wazo-auth-keys/config.yml the updated loader in wazo_auth_keys will accept it (file or directory).
- Use environment variables or Docker secrets for TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN; do not commit real credentials.
- Restart auth/bootstrap after mounting so provisioning applies.

Security note
- Do not commit real secrets to version control. Replace the example values with environment variables or a secrets manager for production use.
- After editing the config, restart the bootstrap / provisioning service so changes are applied.
