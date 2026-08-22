FROM python:3.12-slim AS build
ARG EPISTEMEDIA_ACCEPTED_COMMIT
ARG SOURCE_DATE_EPOCH
ENV EPISTEMEDIA_ACCEPTED_COMMIT=${EPISTEMEDIA_ACCEPTED_COMMIT} \
    SOURCE_DATE_EPOCH=${SOURCE_DATE_EPOCH}
WORKDIR /app
COPY pyproject.toml README.md LICENSE AGENTS.md CONTRIBUTING.md SECURITY.md Makefile Dockerfile compose.yaml ./
COPY .github .github
COPY catalog catalog
COPY constitution constitution
COPY docs docs
COPY governance governance
COPY policies policies
COPY releases releases
COPY research research
COPY schemas schemas
COPY src src
COPY tasks tasks
COPY tests tests
RUN printf '%s\n' "$EPISTEMEDIA_ACCEPTED_COMMIT" | grep -Eq '^[0-9a-f]{40}$' \
    && printf '%s\n' "$SOURCE_DATE_EPOCH" | grep -Eq '^(0|[1-9][0-9]*)$' \
    && python -m pip install --no-cache-dir --prefix=/install '.[server]' \
    && PYTHONPATH=/install/lib/python3.12/site-packages python -m epistemedia validate \
    && PYTHONPATH=/install/lib/python3.12/site-packages python -m epistemedia build --output /app/generated/public

FROM python:3.12-slim
ARG EPISTEMEDIA_ACCEPTED_COMMIT
ARG SOURCE_DATE_EPOCH
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    EPISTEMEDIA_ACCEPTED_COMMIT=${EPISTEMEDIA_ACCEPTED_COMMIT} \
    SOURCE_DATE_EPOCH=${SOURCE_DATE_EPOCH} \
    EPISTEMEDIA_ROOT=/app \
    EPISTEMEDIA_MAX_BODY_BYTES=1048576 \
    EPISTEMEDIA_MAX_QUERY_BYTES=8192 \
    EPISTEMEDIA_MAX_RESPONSE_BYTES=8388608 \
    EPISTEMEDIA_RATE_LIMIT_PER_MINUTE=120 \
    EPISTEMEDIA_REQUEST_TIMEOUT_SECONDS=15 \
    EPISTEMEDIA_ALLOWED_ORIGINS=https://epistemedia.org,https://www.epistemedia.org
WORKDIR /app
COPY --from=build /install /usr/local
COPY --from=build /app /app
RUN useradd --create-home --uid 10001 epistemedia && chown -R epistemedia:epistemedia /app
USER epistemedia
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/healthz', timeout=2)"
CMD ["uvicorn", "epistemedia.server:app", "--host", "0.0.0.0", "--port", "8080", "--no-server-header", "--limit-concurrency", "100", "--backlog", "128", "--timeout-keep-alive", "5"]
