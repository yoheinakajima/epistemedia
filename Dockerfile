FROM python:3.12-slim AS build
WORKDIR /app
COPY . .
RUN python -m pip install --no-cache-dir --prefix=/install '.[server]' \
    && PYTHONPATH=/install/lib/python3.12/site-packages python -m epistemedia validate \
    && PYTHONPATH=/install/lib/python3.12/site-packages python -m epistemedia build --output /app/generated/public

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    EPISTEMEDIA_ROOT=/app
WORKDIR /app
COPY --from=build /install /usr/local
COPY --from=build /app /app
RUN useradd --create-home --uid 10001 epistemedia && chown -R epistemedia:epistemedia /app
USER epistemedia
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/healthz', timeout=2)"
CMD ["uvicorn", "epistemedia.server:app", "--host", "0.0.0.0", "--port", "8080", "--no-server-header"]
