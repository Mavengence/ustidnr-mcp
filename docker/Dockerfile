ARG PYTHON_IMAGE=python:3.11-slim-bookworm

FROM ${PYTHON_IMAGE} AS builder

WORKDIR /app
COPY pyproject.toml .
COPY src/ src/

RUN pip install --no-cache-dir --prefix=/install .

FROM ${PYTHON_IMAGE}

RUN groupadd -r mcp && useradd -r -g mcp mcp
WORKDIR /app

COPY --from=builder /install /usr/local

USER mcp

CMD ["python", "-m", "ustidnr_mcp"]
