# The calculator verifier's environment: the engine's runtime and the docker
# client the cases are run through (each case in the variant's runtime
# image, over the daemon's socket). No compiler, no interpreter here.
FROM python:3.12.3-slim
ARG DOCKER_CLI_VERSION=27.1.1
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
    && arch="$(dpkg --print-architecture)"; case "$arch" in \
        amd64) dc=x86_64 ;; arm64) dc=aarch64 ;; *) dc="$arch" ;; esac; \
    curl -fsSL "https://download.docker.com/linux/static/stable/${dc}/docker-${DOCKER_CLI_VERSION}.tgz" \
      | tar -xz --strip-components=1 -C /usr/local/bin docker/docker \
    && docker --version \
    && apt-get purge -y curl && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*
