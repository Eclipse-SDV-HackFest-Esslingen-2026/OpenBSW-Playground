# OpenBSW SOVD CDA – Dockerfile
#
# Multi-stage build for the Eclipse OpenSOVD Classic Diagnostic Adapter.
# Based on the upstream testcontainer/cda/Dockerfile pattern.
#
# Build:
#   docker build -f real-sovd-cda/Dockerfile \
#     --build-context cda-src=real-sovd-cda/classic-diagnostic-adapter \
#     -t opensovd-cda .
#
# The MDD file and config are copied in at build time.
#
# USE_PREBUILT: set to "1" to skip the Rust build and use the pre-built binary
# checked into real-sovd-cda/bin/opensovd-cda (tracked via Git LFS).
#
#   docker build --build-arg USE_PREBUILT=1 -f real-sovd-cda/Dockerfile -t opensovd-cda .   # fast
#   docker build --build-context cda-src=... -f real-sovd-cda/Dockerfile -t opensovd-cda .  # from source

ARG USE_PREBUILT=0
ARG RUST_VERSION=1.88

# --- Stage 1: Install cargo-chef and sccache ---
FROM rust:${RUST_VERSION}-slim-trixie AS chef
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    pkg-config \
    libssl-dev \
    perl \
    make \
    && rm -rf /var/lib/apt/lists/*
RUN cargo install cargo-chef sccache --locked

# --- Stage 2: Prepare the recipe (dependencies only) ---
FROM chef AS planner
WORKDIR /app
COPY --from=cda-src Cargo.toml Cargo.lock ./
COPY --from=cda-src cda-main/Cargo.toml ./cda-main/Cargo.toml
COPY --from=cda-src cda-interfaces/Cargo.toml ./cda-interfaces/Cargo.toml
COPY --from=cda-src cda-core/Cargo.toml ./cda-core/Cargo.toml
COPY --from=cda-src cda-comm-doip/Cargo.toml ./cda-comm-doip/Cargo.toml
COPY --from=cda-src cda-comm-uds/Cargo.toml ./cda-comm-uds/Cargo.toml
COPY --from=cda-src cda-database/Cargo.toml ./cda-database/Cargo.toml
COPY --from=cda-src cda-plugin-security/Cargo.toml ./cda-plugin-security/Cargo.toml
COPY --from=cda-src cda-sovd/Cargo.toml ./cda-sovd/Cargo.toml
COPY --from=cda-src cda-tracing/Cargo.toml ./cda-tracing/Cargo.toml
COPY --from=cda-src cda-sovd-interfaces/Cargo.toml ./cda-sovd-interfaces/Cargo.toml
COPY --from=cda-src cda-health/Cargo.toml ./cda-health/Cargo.toml
COPY --from=cda-src integration-tests/Cargo.toml ./integration-tests/Cargo.toml
COPY --from=cda-src cda-build/Cargo.toml ./cda-build/Cargo.toml
COPY --from=cda-src comm-mbedtls/mbedtls-rs/Cargo.toml ./comm-mbedtls/mbedtls-rs/Cargo.toml
COPY --from=cda-src comm-mbedtls/mbedtls-sys/Cargo.toml ./comm-mbedtls/mbedtls-sys/Cargo.toml
RUN cargo chef prepare --recipe-path recipe.json

# --- Stage 3: Cook dependencies ---
FROM chef AS cacher
WORKDIR /app
COPY --from=planner /app/recipe.json recipe.json
ENV RUSTC_WRAPPER=sccache \
    SCCACHE_DIR=/sccache
RUN --mount=type=cache,target=/usr/local/cargo/registry,sharing=locked \
    --mount=type=cache,target=/usr/local/cargo/git,sharing=locked \
    --mount=type=cache,target=$SCCACHE_DIR,sharing=locked \
    cargo chef cook --release --recipe-path recipe.json

# --- Stage 4: Build the CDA binary ---
FROM chef AS builder
WORKDIR /app
COPY --from=cacher /app/target target
COPY --from=cacher /usr/local/cargo /usr/local/cargo
COPY --from=cda-src Cargo.toml Cargo.lock ./
COPY --from=cda-src cda-main ./cda-main
COPY --from=cda-src cda-interfaces ./cda-interfaces
COPY --from=cda-src cda-core ./cda-core
COPY --from=cda-src cda-comm-doip ./cda-comm-doip
COPY --from=cda-src cda-comm-uds ./cda-comm-uds
COPY --from=cda-src cda-database ./cda-database
COPY --from=cda-src cda-plugin-security ./cda-plugin-security
COPY --from=cda-src cda-sovd ./cda-sovd
COPY --from=cda-src cda-tracing ./cda-tracing
COPY --from=cda-src cda-sovd-interfaces ./cda-sovd-interfaces
COPY --from=cda-src cda-health ./cda-health
COPY --from=cda-src integration-tests ./integration-tests
COPY --from=cda-src cda-build ./cda-build
COPY --from=cda-src comm-mbedtls ./comm-mbedtls
ARG SOURCE_DATE_EPOCH=0
ARG SOURCE_GIT_SHA=unknown
ENV RUSTC_WRAPPER=sccache \
    SCCACHE_DIR=/sccache \
    SOURCE_DATE_EPOCH=${SOURCE_DATE_EPOCH} \
    SOURCE_GIT_SHA=${SOURCE_GIT_SHA}
RUN --mount=type=cache,target=/usr/local/cargo/registry,sharing=locked \
    --mount=type=cache,target=/usr/local/cargo/git,sharing=locked \
    --mount=type=cache,target=$SCCACHE_DIR,sharing=locked \
    cargo build --release --bin opensovd-cda && \
    cp target/release/opensovd-cda /tmp/opensovd-cda

# --- Stage 5: Runtime ---
FROM debian:trixie-slim AS runtime-base
RUN apt-get update && apt-get install -y --no-install-recommends \
    iproute2 \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
RUN mkdir -p /app/odx /app/flash

# --- Prebuilt path ---
FROM runtime-base AS bin-prebuilt-1
COPY real-sovd-cda/bin/opensovd-cda /app/opensovd-cda

# --- Source-built path ---
FROM runtime-base AS bin-prebuilt-0
COPY --from=builder /tmp/opensovd-cda /app/opensovd-cda

# --- Final: select based on USE_PREBUILT ---
FROM bin-prebuilt-${USE_PREBUILT} AS final

# Copy the OpenBSW MDD file and config
COPY real-sovd-cda/odx-gen/OpenBSW.mdd /app/odx/OpenBSW.mdd
COPY real-sovd-cda/opensovd-cda.toml /app/opensovd-cda.toml
COPY --chmod=755 real-sovd-cda/entrypoint.sh /app/entrypoint.sh

ENV CDA_CONFIG_FILE=/app/opensovd-cda.toml

EXPOSE 8080
ENTRYPOINT ["/app/entrypoint.sh"]
