from flask import Flask, g, request
import random
import time
import logging
from logging.handlers import RotatingFileHandler
import os
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

# Создаем приложение Flask
app = Flask(__name__)

# Пишем логи в stdout для Docker и в общий том, который читает Grafana Alloy.
LOG_DIR = '/var/log/app'
os.makedirs(LOG_DIR, exist_ok=True)
log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
file_handler = RotatingFileHandler(
    os.path.join(LOG_DIR, 'app.log'),
    maxBytes=5 * 1024 * 1024,
    backupCount=3,
    encoding='utf-8',
)
logging.basicConfig(
    level=logging.INFO,
    format=log_format,
    handlers=[logging.StreamHandler(), file_handler],
)
logger = logging.getLogger(__name__)

# Создаем метрики для Prometheus
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP Requests', ['method', 'endpoint', 'status_code'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP Request duration', ['method', 'endpoint'])


@app.before_request
def start_request_timer():
    g.request_started_at = time.perf_counter()


@app.after_request
def record_request_metrics(response):
    # Не считаем скрейпы Prometheus, иначе метрики сами создают трафик.
    if request.path != '/metrics':
        # Unknown paths share a fixed label to prevent unbounded metric cardinality.
        endpoint = request.url_rule.rule if request.url_rule else 'unmatched'
        duration = time.perf_counter() - g.request_started_at
        REQUEST_COUNT.labels(request.method, endpoint, str(response.status_code)).inc()
        REQUEST_DURATION.labels(request.method, endpoint).observe(duration)
        logger.info(
            'HTTP request method=%s path=%s status=%s duration_seconds=%.4f',
            request.method,
            request.path,
            response.status_code,
            duration,
        )
    return response

@app.route('/')
def hello():
    # Логируем информацию о запросе
    logger.info('Hello endpoint was called')
    # Имитация небольшой задержки
    time.sleep(random.uniform(0.1, 0.5))
    return 'Hello, World!'

@app.route('/metrics')
def metrics():
    """Эндпоинт для сбора метрик Prometheus."""
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

@app.route('/health')
def health():
    """Эндпоинт для проверки здоровья сервиса."""
    logger.info('Health check passed')
    return {'status': 'healthy'}, 200


@app.route('/demo-error')
def demo_error():
    """Учебный маршрут для проверки учёта и отображения ответов 5xx."""
    logger.error('Intentional demo error: returning HTTP 500')
    return {'status': 'error', 'message': 'Intentional demo error'}, 500

if __name__ == '__main__':
    # Удобно для локальной разработки; контейнер запускает Gunicorn из Dockerfile.
    app.run(host='0.0.0.0', port=5000)
