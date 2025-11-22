# Dockerfile.cpu
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# system deps for pillow / general image processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential git curl libgl1 libglib2.0-0 libsm6 libxrender1 libxext6 \
    libjpeg-dev libpng-dev && rm -rf /var/lib/apt/lists/*

# copy requirements then install (better layer caching)
COPY requirements-prod.txt /app/requirements-prod.txt

# Install CPU-only torch (latest CPU wheel from PyPI or official index)
RUN pip install --upgrade pip setuptools wheel \
 && pip install --no-cache-dir -r /app/requirements-prod.txt \
 && pip install --no-cache-dir "torch==2.9.1+cpu" -f https://download.pytorch.org/whl/cpu/torch_stable.html

# copy source
COPY . /app

# expose
EXPOSE 8000

# run uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
