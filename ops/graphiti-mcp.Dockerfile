FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

ARG GRAPHITI_GIT_REF=mcp-v1.0.2
WORKDIR /build
RUN apt-get update && apt-get install -y --no-install-recommends git curl ca-certificates && rm -rf /var/lib/apt/lists/*
RUN git clone --depth 1 --branch "${GRAPHITI_GIT_REF}" https://github.com/getzep/graphiti.git /src/graphiti

WORKDIR /src/graphiti/mcp_server
RUN uv sync --extra providers

EXPOSE 8000
CMD ["uv", "run", "main.py", "--transport", "http"]
