#!/usr/bin/env python3
"""
Clone all repositories from a GitHub organization into a destination folder.
Usage:
  ./tools/clone_wazo_repos.py [dest_dir] [org]
Environment:
  GITHUB_TOKEN - optional, for authenticated API calls (higher rate limit)

This script uses the GitHub REST API to list all repos for the org and then
clones each repo (or pulls updates if the repo directory already exists).
"""
import json
import os
import sys
import subprocess
import urllib.request
import urllib.parse


def fetch_repos(org, token=None):
    repos = []
    per_page = 100
    page = 1
    headers = {'User-Agent': 'clone-wazo-repos-script'}
    if token:
        headers['Authorization'] = f'token {token}'
    while True:
        url = f'https://api.github.com/orgs/{urllib.parse.quote(org)}/repos?per_page={per_page}&page={page}'
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as resp:
            data = json.load(resp)
        if not data:
            break
        repos.extend(data)
        if len(data) < per_page:
            break
        page += 1
    return repos


def run(cmd, cwd=None):
    print('>>>', ' '.join(cmd), 'CWD:', cwd)
    r = subprocess.run(cmd, cwd=cwd)
    if r.returncode != 0:
        raise SystemExit(f'Command failed: {cmd} (cwd={cwd})')


def main():
    dest = sys.argv[1] if len(sys.argv) > 1 else './repos'
    org = sys.argv[2] if len(sys.argv) > 2 else os.environ.get('WAZO_ORG', 'wazo-platform')
    token = os.environ.get('GITHUB_TOKEN')

    os.makedirs(dest, exist_ok=True)
    print(f'Cloning repos for org {org} into {dest}')

    repos = fetch_repos(org, token=token)
    print(f'Found {len(repos)} repositories')
    for repo in repos:
        name = repo.get('name')
        clone_url = repo.get('clone_url')
        target = os.path.join(dest, name)
        if os.path.exists(target):
            print(f'Updating {name}')
            try:
                run(['git', 'fetch', '--all'], cwd=target)
                run(['git', 'checkout', 'HEAD'], cwd=target)
                run(['git', 'pull', '--ff-only'], cwd=target)
            except SystemExit as e:
                print('Failed to update', name, e)
        else:
            print(f'Cloning {name} from {clone_url}')
            try:
                run(['git', 'clone', clone_url, target])
            except SystemExit as e:
                print('Failed to clone', name, e)

    print('Done')


if __name__ == '__main__':
    main()
