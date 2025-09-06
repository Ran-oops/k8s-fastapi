from fastapi import FastAPI, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
# from . import crud, models, schemas
# from .database import engine, get_db
# import crud, models, schemas
from app import crud, models, schemas
from app.database import engine, get_db
from prometheus_fastapi_instrumentator import Instrumentator
from app.config import settings
from app.services import redis_service, kafka_producer
from prometheus_client import Counter, Histogram
import time
import logging.config

# --- 日志配置 (ELK) ---
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
        },
    },
    "handlers": {
        "json": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
    },
    "loggers": {
        "": {"handlers": ["json"], "level": "INFO"},
    },
}
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

# --- 创建应用 ---
app = FastAPI(title="Product Review System")

# --- Prometheus 中间件 ---
Instrumentator().instrument(app).expose(app)


# --- Kafka 生产者生命周期事件 ---
@app.on_event("startup")
async def startup_event():
    logger.info("Starting up Kafka producer...")
    await kafka_producer.producer.start()


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Kafka producer...")
    await kafka_producer.producer.stop()


# Dependency
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- API Endpoints ---
@app.post("/products/", response_model=schemas.Product)
def create_product(product: schemas.ProductCreate, db: Session = Depends(get_db)):
    logger.info(f"Creating product with name: {product.name}")
    return crud.create_product(db=db, product=product)


@app.get("/products/{product_id}", response_model=schemas.Product)
def read_product(product_id: int, db: Session = Depends(get_db)):
    logger.info(f"Reading product with id: {product_id}")
    # 1. 检查Redis缓存 (Redis)
    cached_product = redis_service.get_cached_product(product_id)
    if cached_product:
        return cached_product

    # 2. 如果缓存未命中，查询数据库 (PostgreSQL)
    db_product = crud.get_product(db, product_id=product_id)
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    # 3. 将结果写入缓存 (Redis)
    redis_service.set_cached_product(db_product)
    return db_product


@app.post("/reviews/", status_code=202)  # 202 Accepted表示请求已接受，正在处理
async def submit_review(review: schemas.ReviewCreate, db: Session = Depends(get_db)):
    # 检查商品是否存在
    db_product = crud.get_product(db, product_id=review.product_id)
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found for this review")

    # 将评价事件异步发送到Kafka (Kafka)
    await kafka_producer.send_review_to_kafka(review)
    logger.info(f"Review for product {review.product_id} accepted and sent to Kafka.")
    return {"message": "Review submission accepted."}


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

# 创建数据库表
models.Base.metadata.create_all(bind=engine)
"""
当类继承Base时：
    1.sqlalchemy自动检测类属性
    2.将这些属性转换为数据库列定义
    3.将表信息注册到Base.metadata中
"""
"""
create_all(bind=engine) - 表创建命令
    1.扫描Base.metadata中的所有注册表信息
    2.根据数据库类型生成对应的DDL(data definition language)语句
    3.通过指定的engine连接到数据库
    4.执行create table语句
    5.只创建不存在的表，已存在的表不受影响
"""

app = FastAPI()


# 添加中间件来记录自定义指标
@app.middleware("http")
async def monitor_requests(request: Request, call_next):
    start_time = time.time()
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

    return response


# 添加Prometheus监控
Instrumentator().instrument(app).expose(app)


@app.post("/users/", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)


@app.get("/users/", response_model=list[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users


@app.get("/users/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.put("/users/{user_id}", response_model=schemas.User)
def update_user(user_id: int, user_update: schemas.UserUpdate, db: Session = Depends(get_db)):
    db_user = crud.update_user(db, user_id=user_id, user_update=user_update)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.delete("/users/{user_id}", status_code=status.HTTP_200_OK)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    if not crud.delete_user(db, user_id=user_id):
        raise HTTPException(status_code=404, detail="User not found")
    return {"detail": "User deleted successfully"}

# dev运行命令：uvicorn app.main:app --reload
# prod运行命令：uvicorn app.main:app --host 0.0.0.0 --port 80 --workers 4
"""
app.main表示的是app包， main表示module名，即文件名。 :app表示的是main.py中的app = FastAPI()

 --reload
作用：启用开发模式的热重载功能

行为：
    监视项目文件变动（.py, .env 等）
    检测到修改时自动重启服务器
    极大提升开发效率
"""














































































































































