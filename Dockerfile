# ---------- builder ----------
FROM python:3.12-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1 \
    POETRY_HOME="/root/.local" \
    PIP_DEFAULT_TIMEOUT=120 \
    PIP_RETRIES=10 \
    POETRY_HTTP_TIMEOUT=120 \
    PATH="/root/.local/bin:/usr/local/bin:$PATH" \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_ROOT_USER_ACTION=ignore

WORKDIR /app

RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential git curl ca-certificates libgl1 libglib2.0-0 libsm6 libxrender1 libxext6 libjpeg-dev libpng-dev \
 && rm -rf /var/lib/apt/lists/*

# install poetry
RUN curl -sSL https://install.python-poetry.org | python3 - && poetry --version

COPY pyproject.toml poetry.lock /app/

# ensure export plugin
RUN set -eux; \
    if ! poetry self show poetry-plugin-export >/dev/null 2>&1; then \
        poetry self add poetry-plugin-export || python -m pip install --no-cache-dir poetry-plugin-export; \
    fi

# regenerate lock if needed and export, then install into venv
RUN set -eux; \
    if [ ! -f poetry.lock ] || ! poetry check >/dev/null 2>&1; then poetry lock; fi; \
    poetry export -f requirements.txt --without-hashes --output /tmp/requirements.txt; \
    sed -E '/^pywinpty(==|[><~=])/Id' /tmp/requirements.txt | sed -E '/^-e /Id' > /tmp/requirements.clean.txt || true; \
    python -m venv /opt/venv; \
    /opt/venv/bin/python -m pip install --upgrade pip setuptools wheel; \
    n=0; until [ $n -ge 3 ]; do /opt/venv/bin/pip install --no-cache-dir --default-timeout=$PIP_DEFAULT_TIMEOUT --retries=$PIP_RETRIES -r /tmp/requirements.clean.txt && break; n=$((n+1)); sleep 2; done; \
    # CLEANUP: remove caches and broken symlinks/empty files to avoid layer export issues
    rm -rf /root/.cache/pip /tmp/pip-* || true; \
    find /opt/venv/lib/python3.12/site-packages -xtype l -print -delete || true; \
    find /opt/venv/lib/python3.12/site-packages -type f -empty -print -delete || true; \
    # sanity check
    python - <<'PYCODE'
import sys, pkgutil, os
p = '/opt/venv/lib/python3.12/site-packages'
broken = []
for root,dirs,files in os.walk(p):
    for name in dirs+files:
        path = os.path.join(root, name)
        if os.path.islink(path) and not os.path.exists(os.readlink(path) if not os.path.isabs(os.readlink(path)) else os.readlink(path)):
            broken.append(path)
if broken:
    print('BROKEN LINKS:', broken[:10])
    sys.exit(1)
print('site-packages OK')
PYCODE

# ---------- runtime ----------
FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# system runtime deps
RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates libgl1 libglib2.0-0 libsm6 libxrender1 libxext6 libjpeg-dev libpng-dev \
 && rm -rf /var/lib/apt/lists/*

# copy the prepared venv from builder
COPY --from=builder /opt/venv /opt/venv

# copy app
COPY . /app

# non-root user
RUN groupadd -r app && useradd -r -g app -d /home/app -m -s /bin/sh app \
 && chown -R app:app /app /opt/venv

USER app
ENV PATH="/opt/venv/bin:$PATH"

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
