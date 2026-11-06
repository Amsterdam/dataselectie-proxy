FROM ghcr.io/astral-sh/uv:0.13-python3.14-trixie-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app
RUN apt-get update && apt-get install --no-install-recommends -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --all-groups

COPY src/ ./src/

# Start runtime image,
FROM ghcr.io/astral-sh/uv:0.13-python3.14-trixie-slim

RUN useradd -U -r dataselectieproxy
RUN apt-get update && apt-get install --no-install-recommends -y \
    curl \
    libpq5 \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/src
RUN chown dataselectieproxy:dataselectieproxy /app
COPY --from=builder --chown=dataselectieproxy:dataselectieproxy /app /app
USER dataselectieproxy

# Have some defaults so the container is easier to start
ENV DJANGO_SETTINGS_MODULE=dataselectie_proxy.settings \
    DJANGO_DEBUG=false \
    UV_NO_CACHE=1 \
    PYTHONPATH="/app/src" \
    UWSGI_HTTP_SOCKET=:8000 \
    UWSGI_MODULE=dataselectie_proxy.wsgi \
    UWSGI_CALLABLE=application \
    UWSGI_MASTER=1
RUN uv run manage.py collectstatic --noinput

EXPOSE 8000
USER dataselectieproxy
CMD ["uv", "run", "uwsgi"]
