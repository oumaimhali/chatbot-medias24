FROM python:3.11-slim

WORKDIR /app

RUN pip install fastapi uvicorn

COPY test_app.py ./app.py

CMD uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000} --log-level debug
