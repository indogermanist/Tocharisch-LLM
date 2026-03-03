FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=1.8.3 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1 \
    POETRY_REQUESTS_TIMEOUT=300 \
    PIP_DEFAULT_TIMEOUT=300

WORKDIR /app

RUN pip install --no-cache-dir "poetry==$POETRY_VERSION"

COPY pyproject.toml poetry.lock ./
RUN poetry config installer.max-workers 4
RUN for i in 1 2 3; do \
      poetry install --only main --no-root --no-ansi && break || \
      (echo "poetry install failed (attempt $i), retrying..." && sleep 15); \
    done

COPY . .

EXPOSE 8501

CMD ["poetry", "run", "streamlit", "run", "src/streamlit/app.py", "--server.address=0.0.0.0", "--server.port=8501"]
