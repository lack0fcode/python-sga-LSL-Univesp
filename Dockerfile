FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-docker.txt /app/requirements-docker.txt

RUN python -m pip install --upgrade pip setuptools wheel \
    && pip install -r /app/requirements-docker.txt

COPY . /app

RUN chmod +x /app/entrypoint.sh || true

EXPOSE 8000

ENTRYPOINT ["sh", "/app/entrypoint.sh"]
