FROM ghcr.io/nginx/nginx-unprivileged:stable-alpine-slim

COPY web/nginx.conf /etc/nginx/conf.d/default.conf
COPY web/index.html web/app.js web/style.css /usr/share/nginx/html/

USER 101:101
EXPOSE 8080
