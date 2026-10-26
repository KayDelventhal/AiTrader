FROM node:24.22.1-bookworm-slim AS frontend
WORKDIR /build
RUN npm install --global pnpm@10.28.2
COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY frontend/ ./
RUN pnpm build

FROM python:3.12.7-slim-bookworm
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 LANGSMITH_TRACING=false ANONYMIZED_TELEMETRY=false MPLCONFIGDIR=/app/.runtime/matplotlib
COPY requirements.lock ./
RUN pip install --no-cache-dir -r requirements.lock
COPY backend/ backend/
COPY scripts/ scripts/
COPY pyproject.toml ./
COPY --from=frontend /build/dist/ frontend/dist/
RUN useradd --uid 10001 --create-home aitrader && mkdir -p /app/.runtime && chown -R aitrader:aitrader /app
USER aitrader
EXPOSE 8000
CMD ["python", "scripts/container_entrypoint.py"]
