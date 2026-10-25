FROM gcr.io/distroless/python3-debian13:nonroot

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
