FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV GOOGLE_CLOUD_PROJECT=jyothiapikey1
ENV PYTHONPATH=/app
ENV PORT=8080

EXPOSE 8080

WORKDIR /app/api

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
