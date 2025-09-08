#!/bin/sh

set -e # 如果任何命令失败，立即退出脚本

TIMEOUT=5 # 增加超时时间，因为ES启动可能很慢
INTERVAL=5

# 函数：等待TCP端口可用 (保留用于简单服务)
wait_for_port() {
  local HOST=$1
  local PORT=$2
  local SERVICE_NAME=$3
  echo "Waiting for $SERVICE_NAME at $HOST:$PORT..."
  local ELAPSED=0
  while ! nc -z "$HOST" "$PORT"; do
    if [ $ELAPSED -ge $TIMEOUT ]; then
      echo "Timeout waiting for $SERVICE_NAME at $HOST:$PORT."
      exit 1
    fi
    sleep $INTERVAL
    ELAPSED=$((ELAPSED + INTERVAL))
  done
  echo "$SERVICE_NAME is available on TCP port."
}

# 函数：等待Elasticsearch完全就绪 (优化版)
#wait_for_elasticsearch() {
#  local URL=$1
#  echo "Waiting for Elasticsearch at $URL to be healthy..."
#  local ELAPSED=0
#  local RETRY_COUNT=0
#
#  while ! curl -s -f "$URL/_cluster/health?wait_for_status=yellow&timeout=1s" > /dev/null; do
#    if [ $ELAPSED -ge $TIMEOUT ]; then
#      echo "Timeout waiting for Elasticsearch to become healthy."
#      exit 1
#    fi
#
#    # --- 关键修改：优化日志输出 ---
#    # 只在第一次和每隔6次循环(30秒)时打印一次提示
#    if [ $RETRY_COUNT -eq 0 ] || [ $(($RETRY_COUNT % 2)) -eq 0 ]; then
#      echo "Elasticsearch is not healthy yet. Retrying... (waited ${ELAPSED}s)"
#    fi
#
#    sleep $INTERVAL
#    ELAPSED=$((ELAPSED + INTERVAL))
#    RETRY_COUNT=$((RETRY_COUNT + 1))
#  done
#
#  echo "Elasticsearch is healthy."
#}

# --- 执行等待 ---
DB_HOST=${DATABASE_HOST:-postgres-service}
REDIS_HOST=${REDIS_HOST:-redis-service}
KAFKA_HOST=$(echo "${KAFKA_BOOTSTRAP_SERVERS:-kafka-0...local:9092}" | cut -d':' -f1)
KAFKA_PORT=$(echo "${KAFKA_BOOTSTRAP_SERVERS:-kafka-0...local:9092}" | cut -d':' -f2)
ES_URL=${ELASTICSEARCH_URL:-http://elasticsearch-master:9200}

wait_for_port "$DB_HOST" 5432 "PostgreSQL"
wait_for_port "$REDIS_HOST" 6379 "Redis"
wait_for_port "$KAFKA_HOST" "$KAFKA_PORT" "Kafka"
# 使用新的、更智能的健康检查函数来等待ES
wait_for_elasticsearch "$ES_URL"


# --- 启动应用 ---
echo "All dependencies are up. Starting Gunicorn..."

# 启动Gunicorn
exec gunicorn -k uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --threads 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --limit-request-line 8190 \
    app.main:app