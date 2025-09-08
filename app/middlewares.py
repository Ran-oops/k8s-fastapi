# app/middlewares.py (终极版)

import time
from prometheus_client import Counter, Histogram
from fastapi import Request
import logging
from asgi_correlation_id.context import correlation_id

# Prometheus指标定义 (保持不变)
# 创建自定义指标
API_REQUESTS = Counter(
    'myapp_http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'http_status']
)

RESPONSE_TIME = Histogram(
    'http_response_time_seconds',
    'HTTP response time in seconds',
    ['method', 'endpoint'],
    buckets=[0.1, 0.5, 1, 2, 5]
)



# 我们不再需要自己生成UUID，asgi-correlation-id会帮我们做
# 我们也不再需要在这里定义logger，因为我们会直接使用
# from logging import getLogger

async def log_and_monitor_middleware(request: Request, call_next):
    # --- 日志上下文增强 ---
    # asgi-correlation-id中间件已经为我们生成并设置好了ID
    request_id = correlation_id.get()

    # 获取一个普通的logger
    logger = logging.getLogger(__name__)

    # 使用LoggerAdapter来为这个请求的所有后续日志自动添加额外信息
    # 我们把你优秀的日志字段都加到这里
    extra_context = {
        "request_id": request_id,
        "method": request.method,
        "path": request.url.path,
        "client_ip": request.client.host if request.client else "unknown",
        "headers": dict(request.headers)  # 包含headers是个好主意！
    }
    adapter = logging.LoggerAdapter(logger, extra_context)

    start_time = time.time()

    adapter.info("Request started", extra={"event": "request_started"})

    response = await call_next(request)

    process_time = time.time() - start_time
    status_code = response.status_code

    adapter.info(
        "Request finished",
        extra={
            "event": "request_finished",
            "status_code": status_code,
            "process_time_ms": round(process_time * 1000, 2)
        }
    )

    # --- Prometheus 指标记录 (保持不变) ---
    RESPONSE_TIME.labels(method=request.method, endpoint=request.url.path).observe(process_time)
    API_REQUESTS.labels(method=request.method, endpoint=request.url.path, http_status=status_code).inc()

    return response