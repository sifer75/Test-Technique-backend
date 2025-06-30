# Dockerfile pour FastAPI backend

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copier les fichiers requirements (ou poetry/poetry.lock si tu utilises)
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
