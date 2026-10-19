FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN groupadd --gid 10001 app \
    && useradd --uid 10001 --gid 10001 --no-create-home --shell /usr/sbin/nologin app \
    && mkdir -p /var/log/app \
    && chown 10001:10001 /var/log/app

COPY --chown=10001:10001 . .

ENV APP_LOG_DIR=/var/log/app
USER 10001:10001

EXPOSE 5000

CMD ["gunicorn", "--bind=0.0.0.0:5000", "--workers=1", "--worker-class=gthread", "--threads=4", "--access-logfile=-", "--error-logfile=-", "app:app"]
