FROM ghcr.io/astral-sh/uv:python3.12-trixie-slim AS uv

FROM python:3.12-slim-trixie AS builder
COPY --from=uv /usr/local/bin/uv /usr/local/bin/uvx /bin/

WORKDIR /app
RUN apt-get update && apt-get install --no-install-recommends -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-install-project

COPY src/ ./src/
ENV PYTHONPATH=/app/src

# Start runtime image,
FROM python:3.12-slim-trixie
COPY --from=uv /usr/local/bin/uv /usr/local/bin/uvx /bin/

RUN useradd -U -r dataselectieproxy
RUN apt-get update && apt-get install --no-install-recommends -y \
    curl \
    libpq5 \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/.venv /app/.venv
COPY pyproject.toml uv.lock /app/
COPY --from=builder /app/src /app/src

WORKDIR /app/src

# Have some defaults so the container is easier to start
ENV DJANGO_SETTINGS_MODULE=dataselectie_proxy.settings \
    DJANGO_DEBUG=false \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH=/app/src \
    UV_NO_CACHE=1 \
    UWSGI_HTTP_SOCKET=:8000 \
    UWSGI_MODULE=dataselectie_proxy.wsgi \
    UWSGI_CALLABLE=application \
    UWSGI_MASTER=1
RUN uv run --project /app --locked --no-sync python manage.py collectstatic --noinput

EXPOSE 8000
USER dataselectieproxy
CMD ["uv", "run", "--project", "/app", "--locked", "--no-sync", "uwsgi"]
