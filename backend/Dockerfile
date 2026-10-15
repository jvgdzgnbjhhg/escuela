FROM python:3.13-slim-bookworm@sha256:a1165e272e578941b84abc79e4ab38a0305cd12803a5c4247979ac7655f4d641 AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app
RUN groupadd --gid 10001 app && useradd --uid 10001 --gid app --no-create-home app

FROM base AS runtime
COPY requirements.lock ./
RUN pip install --no-cache-dir --require-hashes --only-binary=:all: -r requirements.lock
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./
USER app
EXPOSE 8000
CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]

FROM base AS test
COPY requirements-dev.lock ./
RUN pip install --no-cache-dir --require-hashes --only-binary=:all: -r requirements-dev.lock
COPY app ./app
COPY alembic ./alembic
COPY tests ./tests
COPY alembic.ini pyproject.toml ./
USER app
CMD ["pytest", "-q", "-p", "no:cacheprovider"]
