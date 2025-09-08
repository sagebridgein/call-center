FROM python:3.9-slim
ENV PYTHONUNBUFFERED=1

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    build-essential gcc libpq-dev libldap2-dev libsasl2-dev libssl-dev git ca-certificates \
  && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip
# Minimal deps: alembic (for service migrations), psycopg2-binary and xivo-dao
RUN pip install alembic psycopg2-binary sqlalchemy sqlalchemy-utils requests pyyaml \
  && pip install \
    https://github.com/wazo-platform/xivo-lib-python/archive/master.zip \
    https://github.com/wazo-platform/xivo-dao/archive/master.zip

COPY migrate.py /usr/local/bin/migrate.py
RUN chmod +x /usr/local/bin/migrate.py

WORKDIR /workspace
CMD ["python", "/usr/local/bin/migrate.py"]
