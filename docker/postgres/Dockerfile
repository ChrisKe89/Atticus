FROM postgres:16

ARG PGVECTOR_VERSION=0.8.1
ARG INDEX_MAX_DIMENSIONS=4096

RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        curl \
        gnupg \
        postgresql-server-dev-16; \
    curl -fsSL "https://github.com/pgvector/pgvector/archive/refs/tags/v${PGVECTOR_VERSION}.tar.gz" -o /tmp/pgvector.tar.gz; \
    mkdir -p /tmp/pgvector-src; \
    tar -xzf /tmp/pgvector.tar.gz -C /tmp/pgvector-src --strip-components=1; \
    cd /tmp/pgvector-src; \
    sed -i "s/#define IVFFLAT_MAX_DIM [0-9]\\+/#define IVFFLAT_MAX_DIM ${INDEX_MAX_DIMENSIONS}/" src/ivfflat.h; \
    make PG_CFLAGS="-DIVFFLAT_MAX_DIM=${INDEX_MAX_DIMENSIONS} -DINDEX_MAX_DIMENSIONS=${INDEX_MAX_DIMENSIONS}"; \
    make PG_CFLAGS="-DIVFFLAT_MAX_DIM=${INDEX_MAX_DIMENSIONS} -DINDEX_MAX_DIMENSIONS=${INDEX_MAX_DIMENSIONS}" install; \
    cd /; \
    rm -rf /tmp/pgvector.tar.gz /tmp/pgvector-src; \
    apt-get purge -y --auto-remove \
        build-essential \
        curl \
        gnupg \
        postgresql-server-dev-16; \
    rm -rf /var/lib/apt/lists/*

