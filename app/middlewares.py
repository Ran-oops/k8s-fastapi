import time
import uuid
from prometheus_client import Counter, Histogram
from prometheus_fastapi_instrumentator import Instrumentator
from fastapi import Request
import logging

# 添加中间件来记录自定义指标

logger = logging.getLogger(__name__)

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


async def monitor_requests(request: Request, call_next):
    # 生成请求ID用于跟踪
    request_id = str(uuid.uuid4())
    
    start_time = time.time()
    
    logger.info("Request started", extra={
        "event": "request_started",
        "request_id": request_id,
        "method": request.method,
        "url": str(request.url),
        "client_host": request.client.host,
        "client_port": request.client.port,
        "headers": dict(request.headers)
    })
    
    response = await call_next(request)
    process_time = time.time() - start_time

    # 记录响应时间
    RESPONSE_TIME.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(process_time)

    # 记录请求计数
    API_REQUESTS.labels(
        method=request.method,
        endpoint=request.url.path,
        http_status=response.status_code
    ).inc()
    
    logger.info("Request completed", extra={
        "event": "request_completed",
        "request_id": request_id,
        "method": request.method,
        "url": str(request.url),
        "status_code": response.status_code,
        "process_time": process_time
    })

    return response