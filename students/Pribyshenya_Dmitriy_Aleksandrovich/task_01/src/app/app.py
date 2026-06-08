import os
import sys
import time
import signal
import logging
from datetime import datetime
import redis
from flask import Flask, jsonify, render_template, request

# Настройка структурированного логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Переменные окружения
STU_ID = os.getenv('STU_ID', '220245')
STU_GROUP = os.getenv('STU_GROUP', 'AS-576')
STU_VARIANT = os.getenv('STU_VARIANT', '17')
REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
REDIS_PREFIX = f"stu:{STU_ID}:v{STU_VARIANT}:"

# Graceful shutdown flag
shutdown_flag = False

# Логирование переменных окружения при старте
logger.info(f"Starting application with STU_ID={STU_ID}, STU_GROUP={STU_GROUP}, STU_VARIANT={STU_VARIANT}")
logger.info(f"Redis prefix: {REDIS_PREFIX}")

# Подключение к Redis
try:
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)
    r.ping()
    logger.info("Successfully connected to Redis")
except redis.ConnectionError as e:
    logger.error(f"Failed to connect to Redis: {e}")
    r = None

def signal_handler(signum, frame):
    """Обработчик сигналов для graceful shutdown"""
    global shutdown_flag
    logger.info(f"Received signal {signal.Signals(signum).name}. Starting graceful shutdown...")
    shutdown_flag = True
    
    if r:
        try:
            r.close()
            logger.info("Redis connection closed")
        except Exception as e:
            logger.error(f"Error closing Redis connection: {e}")
    
    logger.info("Graceful shutdown completed")
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

@app.route('/ready')
def health_check():
    """Endpoint для HEALTHCHECK"""
    health_status = {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "service": "flask-app",
        "student": {
            "id": STU_ID,
            "group": STU_GROUP,
            "variant": STU_VARIANT
        }
    }
    
    if r:
        try:
            r.ping()
            health_status["redis"] = "connected"
        except:
            health_status["redis"] = "disconnected"
            health_status["status"] = "degraded"
    else:
        health_status["redis"] = "not_configured"
    
    return jsonify(health_status), 200

@app.route('/')
def index():
    """Главная страница с информацией"""
    visits = 0
    if r:
        try:
            visits_key = f"{REDIS_PREFIX}visits"
            visits = r.incr(visits_key)
            logger.info(f"Incremented visits counter to {visits}")
        except Exception as e:
            logger.error(f"Redis error: {e}")
    
    return render_template('index.html',
                          visits=visits,
                          stu_id=STU_ID,
                          stu_group=STU_GROUP,
                          stu_variant=STU_VARIANT,
                          timestamp=datetime.now().isoformat())

@app.route('/api/info')
def api_info():
    """API endpoint с информацией о студенте"""
    return jsonify({
        "student": {
            "full_name": "Прибышеня Дмитрий Александрович",
            "group": STU_GROUP,
            "student_id": STU_ID,
            "variant": STU_VARIANT
        },
        "redis_prefix": REDIS_PREFIX,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/cache/<key>')
def get_cache(key):
    """Получение значения из кэша"""
    if not r:
        return jsonify({"error": "Redis not available"}), 503
    
    cache_key = f"{REDIS_PREFIX}{key}"
    value = r.get(cache_key)
    
    if value:
        return jsonify({"key": key, "value": value, "cached": True})
    return jsonify({"key": key, "value": None, "cached": False})

@app.route('/api/cache/<key>', methods=['POST'])
def set_cache(key):
    """Установка значения в кэш"""
    if not r:
        return jsonify({"error": "Redis not available"}), 503
    
    value = request.json.get('value', '')
    cache_key = f"{REDIS_PREFIX}{key}"
    r.set(cache_key, value)
    logger.info(f"Set cache key {cache_key} = {value}")
    
    return jsonify({"key": key, "value": value, "cached": True})

@app.before_request
def log_request():
    """Логирование входящих запросов"""
    logger.info(f"Request: {request.method} {request.path} from {request.remote_addr}")

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def server_error(e):
    logger.error(f"Server error: {e}")
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    logger.info("Starting Flask application on port 9051")
    app.run(host='0.0.0.0', port=9051, debug=False)