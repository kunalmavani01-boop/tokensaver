FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV HEADROOM_REQUIRE_RUST_CORE=false
ENV HEADROOM_TELEMETRY=off

EXPOSE 3001

CMD uvicorn manager.server:app --host 0.0.0.0 --port 3001
