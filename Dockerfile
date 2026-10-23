# the official uv image, pinned, so builds don't drift with python:latest
FROM ghcr.io/astral-sh/uv:0.13.5-python3.13-trixie-slim

# bytecode is compiled once here, and copying beats hardlinking out of the build cache
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_NO_DEV=1

WORKDIR /app

# dependencies get their own layer, so a code change doesn't reinstall them
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-install-project

COPY . .
RUN uv sync --locked

RUN useradd --system --no-create-home takina
USER takina

ENV PATH="/app/.venv/bin:$PATH"
CMD ["python", "-m", "takina"]
