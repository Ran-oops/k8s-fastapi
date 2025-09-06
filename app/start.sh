#!/bin/bash

# 等待数据库等依赖服务就绪
# while ! nc -z $DB_HOST $DB_PORT; do
#   sleep 1
# done

# 执行数据库迁移
# alembic upgrade head

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