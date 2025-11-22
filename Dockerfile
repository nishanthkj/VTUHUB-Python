# Dockerfile.fix-export
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1 \
    POETRY_HOME="/opt/poetry" \
    PIP_DEFAULT_TIMEOUT=120 \
    PIP_RETRIES=10 \
    POETRY_HTTP_TIMEOUT=120

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential git curl ca-certificates libgl1 libglib2.0-0 libsm6 libxrender1 libxext6 \
    libjpeg-dev libpng-dev && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 - \
 && ln -s /root/.local/bin/poetry /usr/local/bin/poetry
ENV PATH="$POETRY_HOME/bin:$PATH"

# Copy pyproject + lock
COPY pyproject.toml poetry.lock /app/

# Ensure export plugin exists (try poetry self add; fall back to pip install)
RUN set -eux; \
    if poetry self show poetry-plugin-export >/dev/null 2>&1; then \
        echo "export plugin already present"; \
    else \
        # try poetry self add (works with Poetry >=1.2+)
        poetry self add poetry-plugin-export || \
        # fallback: install plugin via pip into the same Python
        python -m pip install --no-cache-dir poetry-plugin-export; \
    fi

# Export requirements and install with pip (retries)
RUN set -eux; \
    poetry export -f requirements.txt --without-hashes --output /tmp/requirements.txt || (sleep 2 && poetry export -f requirements.txt --without-hashes --output /tmp/requirements.txt); \
    n=0; until [ $n -ge 3 ]; do \
        pip install --default-timeout=$PIP_DEFAULT_TIMEOUT --retries=$PIP_RETRIES -r /tmp/requirements.txt && break; \
        n=$((n+1)); sleep 5; \
    done

# Install CPU-only torch explicitly
RUN pip install --no-cache-dir "torch==2.9.1+cpu" -f https://download.pytorch.org/whl/cpu/torch_stable.html

COPY . /app

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
