FROM python:3.13-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY . /app/
WORKDIR /app/

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates bash ffmpeg git zip build-essential python3-dev libssl-dev libffi-dev pkg-config \
    && uv sync --frozen --no-install-project \
    && apt-get remove -y --purge build-essential python3-dev libssl-dev libffi-dev pkg-config \
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Add .venv/bin to PATH
ENV PATH="/app/.venv/bin:$PATH"

CMD ["bash", "start"]
