FROM python:3.11.7-slim AS compile-image
RUN apt-get update && apt-get install -y --no-install-recommends build-essential gcc && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11.7-slim AS build-image
COPY --from=compile-image /opt/venv /opt/venv

WORKDIR /app
COPY . .

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

EXPOSE 8000

ENV PATH="/opt/venv/bin:$PATH"

CMD ["python", "-m", "gunicorn", "kafkaworker.asgi:application", "-k", "uvicorn.workers.UvicornWorker"]
