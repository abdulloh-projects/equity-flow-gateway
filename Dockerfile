FROM python:3.13-slim AS builder

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir grpcio-tools

RUN bash src/scripts/generate_protos.sh

FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir pytest pytest-asyncio httpx

COPY --from=builder /app/src ./src

COPY tests ./tests
COPY pytest.ini .

ENV PYTHONPATH=/app/src

CMD ["uvicorn", "apps.main:app", "--host", "0.0.0.0", "--port", "8080"]
