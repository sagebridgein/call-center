#!/usr/bin/env python3
import os
import sys
import time
from urllib.parse import urlparse

DB_URI = os.getenv('WAZO_DB_URI') or os.getenv('DATABASE_URL') or os.getenv('POSTGRES_URI')
if not DB_URI:
    user = os.getenv('POSTGRES_USER', 'asterisk')
    pwd = os.getenv('POSTGRES_PASSWORD', 'secret')
    host = os.getenv('DB_HOST', os.getenv('POSTGRES_HOST', 'postgres'))
    db = os.getenv('POSTGRES_DB', 'wazo')
    DB_URI = f'postgresql://{user}:{pwd}@{host}/{db}'

import datetime

def ts():
    return datetime.datetime.utcnow().isoformat() + 'Z'

print(f"{ts()} Using DB URI: {DB_URI}")

# Retry logic for DB availability
def wait_for_db(uri, retries=30, delay=1):
    from sqlalchemy import create_engine
    for i in range(retries):
        try:
            e = create_engine(uri)
            conn = e.connect()
            conn.close()
            print(f"{ts()} DB reachable")
            return True
        except Exception as exc:
            print(f"{ts()} DB not reachable yet: {exc}")
            time.sleep(delay)
    return False

if not wait_for_db(DB_URI):
    print('DB unreachable, aborting')
    sys.exit(1)

# Run xivo_dao init_db to create core tables used by services that use xivo_dao
try:
    # init_db will create essential DAOs and ensure minimal tables exist.
    from xivo_dao.helpers.db_manager import init_db
    print(f"{ts()} Running xivo_dao.init_db...")
    init_db(DB_URI)
    print(f"{ts()} xivo_dao.init_db finished")
except Exception as e:
    # Non-fatal: we continue to best-effort run alembic migrations.
    print(f"{ts()} xivo_dao.init_db raised: {type(e)} {e}")

# As a pragmatic one-shot: ensure SQLAlchemy models are present in the DB.
# Some projects rely on alembic migrations which may not be available inside
# this container; create_all will create missing tables defined by models
# (including `infos`) so services like confd won't fail at first request.
try:
    from sqlalchemy import create_engine
    from xivo_dao.helpers.db_manager import Base
    print(f"{ts()} Ensuring model tables exist via metadata.create_all...")
    # Ensure model modules are imported so their Table metadata is registered
    try:
        import pkgutil
        import importlib
        import xivo_dao.alchemy as _alchemy
        print('Discovering xivo_dao.alchemy modules to import...')
        for _finder, modname, _ispkg in pkgutil.iter_modules(_alchemy.__path__):
            try:
                importlib.import_module(f"{_alchemy.__name__}.{modname}")
                print('imported', modname)
            except Exception as ie:
                print('failed to import', modname, type(ie), ie)
    except Exception as de:
        print('alchemy discovery/import failed:', type(de), de)

    engine = create_engine(DB_URI)
    # Only create the minimal `infos` table to satisfy confd's immediate need.
    try:
        # Import the Infos model by loading the source file directly to avoid
        # executing xivo_dao.alchemy.__init__ (which imports many modules and
        # can fail when dependent tables are missing).
        import xivo_dao
        import importlib.util
        infos_path = os.path.join(list(xivo_dao.__path__)[0], 'alchemy', 'infos.py')
        print(f"{ts()} Attempting to load Infos from {infos_path}")
        spec = importlib.util.spec_from_file_location('xivo_dao_alchemy_infos_tmp', infos_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        Infos = getattr(mod, 'Infos')
        print(f"{ts()} Creating table for Infos only...")
        Infos.__table__.create(bind=engine, checkfirst=True)
        print(f"{ts()} Infos table ensured")
    except Exception as ie:
        print(f"{ts()} Ensuring Infos table failed: {type(ie)} {ie}")
except Exception as e:
    print('create_all failed:', type(e), e)

# (Deprecated) earlier this script attempted to run alembic programmatically for
# a small hardcoded list of services. That approach had path resolution issues
# ("Path doesn't exist: alembic") for some repos. We now rely on the
# discover+run_subprocess flow implemented below which runs alembic in a
# per-repo venv with cwd set to the repo root so relative `script_location`
# entries are resolved correctly.

def discover_alembic_files(root_path='/home/ubuntu', maxdepth=4):
    matches = []
    for dirpath, dirnames, filenames in os.walk(root_path):
        # compute depth
        rel = os.path.relpath(dirpath, root_path)
        depth = 0 if rel == '.' else rel.count(os.sep) + 1
        if depth > maxdepth:
            # don't walk deeper
            dirnames[:] = []
            continue
        if 'alembic.ini' in filenames:
            matches.append(os.path.join(dirpath, 'alembic.ini'))
            print(f"{ts()} Found alembic.ini: {os.path.join(dirpath, 'alembic.ini')}")
    return matches


def find_repo_root(start_dir):
    root = start_dir
    while root and root != '/' and root != '/home/ubuntu':
        if os.path.exists(os.path.join(root, 'setup.py')) or os.path.exists(os.path.join(root, 'pyproject.toml')):
            return root
        parent = os.path.dirname(root)
        if parent == root:
            break
        root = parent
    # fallback to start_dir
    return start_dir


def run_subprocess(cmd, env=None, cwd=None, logger=None):
    """Run subprocess command, return (success, stdout). Logs to stdout and to logger if provided.

    Args:
      cmd: list of command tokens
      env: environment dict or None
      cwd: working directory or None
      logger: file-like object to append logs (optional)
    """
    import subprocess
    line = f">>> {ts()} CMD: {' '.join(cmd)}" + (f'  CWD: {cwd}' if cwd else '')
    print(line)
    if logger:
        logger.write(line + "\n")
    try:
        r = subprocess.run(cmd, env=env, cwd=cwd, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        print(r.stdout)
        if logger:
            logger.write(r.stdout + "\n")
        return True, r.stdout
    except subprocess.CalledProcessError as e:
        err = f'Command failed: {e.returncode}'
        print(f"{ts()} {err}")
        if logger:
            logger.write(err + "\n")
        if e.stdout:
            print(e.stdout)
            if logger:
                logger.write(e.stdout + "\n")
        return False, e.stdout or ''


def run_alembic_for_cfg(cfg_path, db_uri, logger=None, log_dir=None):
    # compute repo root
    cfg_dir = os.path.dirname(cfg_path)
    repo_root = find_repo_root(cfg_dir)
    summary_line = f'--- Running alembic for {cfg_path} repo_root={repo_root} ---'
    print('\n' + summary_line)
    if logger:
        logger.write(f"{ts()} {summary_line}\n")
    if logger:
        logger.write('\n' + summary_line + '\n')

    # prepare per-repo log file if requested
    per_repo_logf = None
    try:
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
            per_name = os.path.basename(repo_root.rstrip('/')) or 'repo'
            per_log_path = os.path.join(log_dir, f'{per_name}.log')
            # rotate if file is too big
            try:
                if os.path.exists(per_log_path) and os.path.getsize(per_log_path) > 5 * 1024 * 1024:
                    # rotate: keep 5 files
                    for i in range(4, 0, -1):
                        older = f"{per_log_path}.{i}"
                        if os.path.exists(older):
                            os.rename(older, f"{per_log_path}.{i+1}")
                    os.rename(per_log_path, f"{per_log_path}.1")
                    # remove oldest
                    if os.path.exists(f"{per_log_path}.6"):
                        os.remove(f"{per_log_path}.6")
            except Exception as e:
                print(f"{ts()} Log rotation failed for {per_log_path}: {e}")
            per_repo_logf = open(per_log_path, 'a', buffering=1)
            if logger:
                logger.write(f'Per-repo log: {per_log_path}\n')
    except Exception as e:
        print('Failed to open per-repo log file:', e)
        if logger:
            logger.write(f'Failed to open per-repo log file: {e}\n')
    # create ephemeral venv per repo
    import tempfile
    import hashlib
    import glob
    import shutil

    # venv caching: compute a cache key based on requirements.txt contents
    def _requirements_hash(path):
        req = os.path.join(path, 'requirements.txt')
        if os.path.exists(req):
            with open(req, 'rb') as fh:
                data = fh.read()
        else:
            # fallback marker when no requirements.txt
            data = b'alembic-only'
        h = hashlib.sha256()
        h.update(data)
        # include python executable path so different Python ABIs won't collide
        h.update(sys.executable.encode('utf-8'))
        return h.hexdigest()

    cache_root = os.environ.get('MIGRATOR_VENV_CACHE', '/tmp/migrator_venv_cache')
    try:
        os.makedirs(cache_root, exist_ok=True)
    except Exception:
        cache_root = None

    cache_key = None
    venv_dir = None
    if cache_root:
        try:
            cache_key = _requirements_hash(repo_root)
            venv_dir = os.path.join(cache_root, cache_key)
        except Exception as e:
            print(f"{ts()} Failed computing requirements hash: {e}")
            venv_dir = None

    created_cached = False
    if venv_dir and os.path.exists(venv_dir):
        print(f"{ts()} Reusing cached venv at {venv_dir}")
        ok = True
        # set bin paths when reusing a cached venv
        try:
            python_bin = os.path.join(venv_dir, 'bin', 'python')
            pip_bin = os.path.join(venv_dir, 'bin', 'pip')
            alembic_bin = os.path.join(venv_dir, 'bin', 'alembic')
        except Exception:
            python_bin = sys.executable
            pip_bin = 'pip'
            alembic_bin = 'alembic'
    else:
        # create a temporary venv if no cached venv exists (or cannot use cache)
        venv_dir = tempfile.mkdtemp(prefix='migrator_venv_')
        print(f"{ts()} Creating venv at {venv_dir}")
        ok, out = run_subprocess([sys.executable, '-m', 'venv', venv_dir], logger=per_repo_logf or logger)
        if not ok:
            print('Failed to create venv, falling back to system python')
            python_bin = sys.executable
            pip_bin = 'pip'
            alembic_bin = 'alembic'
        else:
            python_bin = os.path.join(venv_dir, 'bin', 'python')
            pip_bin = os.path.join(venv_dir, 'bin', 'pip')
            alembic_bin = os.path.join(venv_dir, 'bin', 'alembic')
        # if we have a cache root and a cache_key, move the freshly created venv into cache
        if ok and cache_root and cache_key:
            try:
                cached_target = os.path.join(cache_root, cache_key)
                if os.path.exists(cached_target):
                    # race: another process created it; remove our temp and reuse
                    shutil.rmtree(venv_dir)
                    venv_dir = cached_target
                    print(f"{ts()} Another process created cache; reusing {venv_dir}")
                else:
                    shutil.move(venv_dir, cached_target)
                    venv_dir = cached_target
                    created_cached = True
                    print(f"{ts()} Stored venv into cache {venv_dir}")
                python_bin = os.path.join(venv_dir, 'bin', 'python')
                pip_bin = os.path.join(venv_dir, 'bin', 'pip')
                alembic_bin = os.path.join(venv_dir, 'bin', 'alembic')
            except Exception as e:
                print(f"{ts()} Failed to move venv into cache: {e}")

    # install requirements if present, otherwise ensure alembic is installed
    requirements = os.path.join(repo_root, 'requirements.txt')
    if os.path.exists(requirements):
        print(f"{ts()} Installing requirements from {requirements}")
        # use python -m pip to avoid relying on a pip binary existing in venv
        run_subprocess([python_bin, '-m', 'pip', 'install', '--no-cache-dir', '-r', requirements], logger=per_repo_logf or logger)
    else:
        print(f"{ts()} No requirements.txt in {repo_root} - installing alembic into venv")
        run_subprocess([python_bin, '-m', 'pip', 'install', 'alembic'], logger=per_repo_logf or logger)

    # Run alembic with env
    env = os.environ.copy()
    env['ALEMBIC_DB_URI'] = db_uri
    # set PYTHONPATH so service package is importable
    env['PYTHONPATH'] = repo_root

    if os.path.exists(alembic_bin):
        alembic_cmd = [alembic_bin, '-c', cfg_path, 'upgrade', 'head']
    else:
        alembic_cmd = [python_bin, '-m', 'alembic', '-c', cfg_path, 'upgrade', 'head']
    success, output = run_subprocess(alembic_cmd, env=env, cwd=repo_root, logger=per_repo_logf or logger)
    if success:
        msg = f'alembic upgrade succeeded for {cfg_path}'
        print(f"{ts()} {msg}")
        if logger:
            logger.write(msg + '\n')
    else:
        msg = f'alembic upgrade FAILED for {cfg_path}'
        print(f"{ts()} {msg}")
        if logger:
            logger.write(msg + '\n')
    # cleanup ephemeral venv only when it is truly ephemeral (not cached)
    try:
        import shutil
        if cache_root and cache_key and os.path.exists(os.path.join(cache_root, cache_key)) and not created_cached:
            # We reused a cached venv; nothing to remove
            pass
        else:
            # remove the temporary venv we created
            if venv_dir and os.path.exists(venv_dir) and '/migrator_venv_' in venv_dir:
                shutil.rmtree(venv_dir)
                print(f"{ts()} Removed venv {venv_dir}")
                if logger:
                    logger.write(f'Removed venv {venv_dir}\n')
    except Exception as re:
        print(f"{ts()} Failed to remove venv {venv_dir} {re}")
        if logger:
            logger.write(f'Failed to remove venv {venv_dir}: {re}\n')
    finally:
        if per_repo_logf:
            try:
                per_repo_logf.close()
            except Exception:
                pass
    return success


def main_run_all_migrations(db_uri, logger=None, log_dir=None, fail_fast=False):
    """Discover alembic.ini files and run migrations for each one.

    logger: optional file-like object to append logs to.
    """
    cfgs = discover_alembic_files('/home/ubuntu', maxdepth=5)
    if not cfgs:
        print(f"{ts()} No alembic.ini found under /home/ubuntu")
        return
    failures = []
    for cfg in cfgs:
        try:
            ok = run_alembic_for_cfg(cfg, db_uri, logger=logger, log_dir=log_dir)
            if not ok:
                failures.append(cfg)
                if fail_fast:
                    if logger:
                        logger.write(f'Fail-fast enabled, aborting after failure in {cfg}\n')
                    break
        except Exception as e:
            failures.append(cfg)
            print('Unhandled error running alembic for', cfg, type(e), e)
            if logger:
                logger.write(f'Unhandled error running alembic for {cfg}: {type(e)} {e}\n')
            if fail_fast:
                break
    return failures


if __name__ == '__main__':
    # run automated migrations after the pragmatic fixes above
    # ensure log directory exists
    log_dir = '/var/log/db-migrator'
    try:
        os.makedirs(log_dir, exist_ok=True)
    except Exception:
        # fallback to /tmp when running without privileges
        log_dir = '/tmp'
    log_path = os.path.join(log_dir, 'migrator.log')
    print('Writing migrator log to', log_path)
    # rotate main migrator log if it grows too large
    try:
        if os.path.exists(log_path) and os.path.getsize(log_path) > 5 * 1024 * 1024:
            for i in range(4, 0, -1):
                older = f"{log_path}.{i}"
                if os.path.exists(older):
                    os.rename(older, f"{log_path}.{i+1}")
            os.rename(log_path, f"{log_path}.1")
            if os.path.exists(f"{log_path}.6"):
                os.remove(f"{log_path}.6")
    except Exception as e:
        print(f"{ts()} Failed to rotate migrator log: {e}")

    try:
        with open(log_path, 'a', buffering=1) as logf:
            logf.write('\n--- db-migrator run starting ---\n')
            # create per-repo logs under the workspace so they are persisted to the host when mounted
            failures = main_run_all_migrations(DB_URI, logger=logf, log_dir=os.path.join(os.getcwd(), 'migrator_logs'), fail_fast=True)
            logf.write('--- db-migrator run finished ---\n')
            if failures:
                logf.write('FAILURES:\n')
                for f in failures:
                    logf.write(f + '\n')
    except Exception as e:
        print('Failed to open/write log file', log_path, e)
        # still run migrations without logger
        failures = main_run_all_migrations(DB_URI, fail_fast=True)

    if failures:
        print('Migrations had failures:', failures)
        sys.exit(2)

    print('db-migrator finished')
