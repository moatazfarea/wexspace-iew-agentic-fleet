FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app
COPY requirements.txt pyproject.toml ./
COPY src ./src
COPY security ./security
COPY data/UTL-NET-001_SYNTHETIC_INPUT.json ./data/UTL-NET-001_SYNTHETIC_INPUT.json
RUN pip install --no-cache-dir .

CMD ["sh", "-c", "uvicorn wexspace.api:app --host 0.0.0.0 --port ${PORT}"]

