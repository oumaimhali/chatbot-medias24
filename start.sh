#!/bin/bash
echo "Starting application..."
echo "PORT: ${PORT:-8000}"
echo "Working directory: $(pwd)"
echo "Files in current directory:"
ls -la

PORT="${PORT:-8000}"
echo "Starting uvicorn with port $PORT"
uvicorn app:app --host 0.0.0.0 --port $PORT --log-level debug
