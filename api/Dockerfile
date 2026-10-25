FROM python:3.13-slim-trixie

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

ARG APP_VERSION=dev
ENV APP_VERSION=${APP_VERSION}

WORKDIR /app
COPY api/opsboard/ /app/opsboard/

USER 10001:10001
EXPOSE 8080
CMD ["python", "-m", "opsboard.app"]
