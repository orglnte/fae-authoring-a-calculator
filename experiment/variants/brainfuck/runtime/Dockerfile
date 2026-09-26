# The brainfuck runtime: tritium `bfi` (rdebath/Brainfuck, tag v1.2) built
# from source, run as `bfi -b32 -z <program>` — 32-bit cells, `,` reads 0 at
# end of input. Nothing else lives here: the program under judgment is
# mounted in and the container has no network.
FROM debian:bookworm-slim AS build
ARG BF_COMMIT=cf310c9429f998a38ba9be4449a8bfdfad58c896
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc libc6-dev make curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*
RUN mkdir /src \
    && curl -fsSL "https://github.com/rdebath/Brainfuck/archive/${BF_COMMIT}.tar.gz" \
       | tar -xz -C /src --strip-components=1 \
    && cd /src/tritium \
    && make VERSION=v1.2 DO_TCC= DO_LIGHT= DO_LIGHT2= DO_MYLIGHT= \
            DO_LIBDL1= DO_LIBDL2= DO_DYNASM= bfi \
    && ./bfi -h 2>&1 | grep -q -- '-b32'

FROM debian:bookworm-slim
COPY --from=build /src/tritium/bfi /usr/local/bin/bfi
