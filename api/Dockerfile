# Temporary security overlay for Debian DSA-6613-1 (CVE-2026-76844 / CVE-2026-85091).
# Distroless has no package manager. Download only the fixed zlib1g Debian package
# and transplant its files plus scanner-visible metadata into the runtime image.
# Remove this stage once the upstream distroless base ships the patched package.
FROM debian:trixie-slim AS patched-zlib

RUN set -eu; \
    apt-get update; \
    mkdir -p /tmp/zlib-deb /patched-root/var/lib/dpkg/status.d; \
    cd /tmp/zlib-deb; \
    apt-get download zlib1g; \
    set -- zlib1g_*.deb; \
    test "$#" -eq 1 && test -f "$1"; \
    version="$(dpkg-deb -f "$1" Version)"; \
    dpkg --compare-versions "$version" ge '1:1.3.dfsg+really1.3.1-1+deb13u1'; \
    dpkg-deb -x "$1" /patched-root; \
    dpkg-deb -f "$1" > /patched-root/var/lib/dpkg/status.d/zlib1g; \
    dpkg-deb -e "$1" /tmp/zlib-deb/control; \
    if [ -f /tmp/zlib-deb/control/md5sums ]; then \
        cp /tmp/zlib-deb/control/md5sums /patched-root/var/lib/dpkg/status.d/zlib1g.md5sums; \
    fi

FROM gcr.io/distroless/python3-debian13:nonroot

# Preserve the minimal nonroot runtime while updating the vulnerable library.
COPY --from=patched-zlib /patched-root/ /

ENV PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

# Build-time defaults for reproducible teaching releases.
# Normal production builds keep readiness enabled.
ARG APP_VERSION=dev
ARG TP_READINESS=true
ARG TP_BANNER="Kubernetes est prêt !"
ENV APP_VERSION=${APP_VERSION} \
    OPSBOARD_READY=${TP_READINESS} \
    MESSAGE_BANNIERE="${TP_BANNER}"

WORKDIR /app
COPY api/opsboard/ /app/opsboard/

USER 65532:65532
EXPOSE 8080
ENTRYPOINT ["/usr/bin/python3"]
CMD ["-m", "opsboard.app"]
