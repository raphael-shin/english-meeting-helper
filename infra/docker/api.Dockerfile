FROM python:3.11-slim AS base
WORKDIR /app
COPY apps/api/requirements.txt apps/api/requirements.txt
RUN pip install --no-cache-dir -r apps/api/requirements.txt
COPY apps/api app/api
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
