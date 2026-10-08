FROM ghcr.io/astral-sh/uv:0.12.23 AS uv

FROM ubuntu:24.04 AS dev
ARG DEBIAN_FRONTEND=noninteractive
ARG LOCAL_UID=1000
ARG LOCAL_GID=1000

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates git curl build-essential cmake ninja-build gdb pkg-config \
    python3 python3-venv python3-dev \
    clang-20 libc++-20-dev libc++abi-20-dev \
    && rm -rf /var/lib/apt/lists/*
COPY --from=uv /uv /uvx /usr/local/bin/

# Replace the base image's optional default user with the workspace user.
RUN if id ubuntu >/dev/null 2>&1; then userdel -r ubuntu; fi \
    && if getent group ubuntu >/dev/null; then groupdel ubuntu; fi \
    && groupadd --gid "${LOCAL_GID}" dev \
    && useradd --uid "${LOCAL_UID}" --gid "${LOCAL_GID}" --create-home --shell /bin/bash dev \
    && mkdir -p /workspace/output /workspace/.venv \
    && chown -R dev:dev /workspace

ENV UV_PROJECT_ENVIRONMENT=/workspace/.venv \
    UV_PYTHON_DOWNLOADS=never \
    UV_LINK_MODE=copy \
    PATH=/workspace/.venv/bin:$PATH
USER dev
WORKDIR /workspace
CMD ["bash"]
