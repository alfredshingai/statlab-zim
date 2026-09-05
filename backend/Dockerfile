# Backend Dockerfile — expects build context = repository root
# Build with: docker build -f backend/Dockerfile -t statlab-backend .
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

# Install backend deps
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared src + backend code
COPY src ./src
COPY backend ./backend
COPY requirements.txt ./requirements-root.txt

ENV PYTHONPATH=/app:/app/backend
WORKDIR /app/backend

EXPOSE 8000

# Run migrations / create tables then start
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
