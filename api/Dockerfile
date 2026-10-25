FROM gcr.io/distroless/python3-debian13:nonroot

ENV PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

ARG APP_VERSION=dev
ENV APP_VERSION=${APP_VERSION}

WORKDIR /app
COPY api/opsboard/ /app/opsboard/

USER 65532:65532
EXPOSE 8080
ENTRYPOINT ["/usr/bin/python3"]
CMD ["-m", "opsboard.app"]
