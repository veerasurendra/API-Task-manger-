FROM python:3.11-slim

WORKDIR /code

# System deps (kept minimal since SQLite driver ships with Python)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# SQLite data lives here; mount a volume in docker-compose to persist it
RUN mkdir -p /code/data

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
