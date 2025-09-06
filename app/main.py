# 1. Standard Library Imports
import logging.config
import uuid
from contextlib import asynccontextmanager

# 2. Third-Party Library Imports
from fastapi import FastAPI, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

# 3. Local Application/Library Imports
from . import crud, schemas
from .database import get_db, create_db_and_tables
from .services import kafka_producer, redis_service
from .middlewares import monitor_requests

# --- 日志配置 (ELK) ---
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s %(pathname)s %(lineno)d %(funcName)s",
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

# --- Lifespan 管理器 ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 在应用启动时运行
    logger.info("Application startup...", extra={"startup": True, "event": "startup"})
    create_db_and_tables()
    logger.info("Database tables checked/created.", extra={"db_init": True})
    logger.info("Starting up Kafka producer...", extra={"kafka": "starting"})
    await kafka_producer.producer.start()

    yield

    # 在应用关闭时运行
    logger.info("Application shutdown...", extra={"shutdown": True, "event": "shutdown"})
    logger.info("Shutting down Kafka producer...", extra={"kafka": "stopping"})
    await kafka_producer.producer.stop()

# --- 创建应用实例并注册lifespan ---
app = FastAPI(
    title="Product Review System",
    lifespan=lifespan
)
app.middleware("http")(monitor_requests) # 注册方式略有不同

# --- Prometheus 中间件 ---
# Instrumentator().instrument(app).expose(app)



# --- API Endpoints ---
@app.post("/products/", response_model=schemas.Product)
def create_product(product: schemas.ProductCreate, db: Session = Depends(get_db)):
    logger.info("Creating product", extra={
        "event": "create_product",
        "product_name": product.name,
        "product_description": product.description
    })
    db_product = crud.create_product(db=db, product=product)
    logger.info("Product created successfully", extra={
        "event": "product_created",
        "product_id": db_product.id,
        "product_name": db_product.name
    })
    return db_product


@app.get("/products/{product_id}", response_model=schemas.Product)
def read_product(product_id: int, db: Session = Depends(get_db)):
    logger.info("Reading product", extra={
        "event": "read_product",
        "product_id": product_id
    })
    # 1. 检查Redis缓存 (Redis)
    cached_product = redis_service.get_cached_product(product_id)
    if cached_product:
        logger.info("Product found in cache", extra={
            "event": "cache_hit",
            "product_id": product_id
        })
        return cached_product

    # 2. 如果缓存未命中，查询数据库 (PostgreSQL)
    db_product = crud.get_product(db, product_id=product_id)
    if db_product is None:
        logger.warning("Product not found", extra={
            "event": "product_not_found",
            "product_id": product_id
        })
        raise HTTPException(status_code=404, detail="Product not found")

    # 3. 将结果写入缓存 (Redis)
    redis_service.set_cached_product(db_product)
    logger.info("Product retrieved from database and cached", extra={
        "event": "cache_miss",
        "product_id": product_id
    })
    return db_product


@app.post("/reviews/", status_code=202)  # 202 Accepted表示请求已接受，正在处理
async def submit_review(review: schemas.ReviewCreate, db: Session = Depends(get_db)):
    logger.info("Processing review submission", extra={
        "event": "submit_review",
        "product_id": review.product_id,
        "user_id": review.user_id,
        "rating": review.rating
    })
    # 检查商品是否存在
    db_product = crud.get_product(db, product_id=review.product_id)
    if db_product is None:
        logger.warning("Product not found for review", extra={
            "event": "product_not_found_for_review",
            "product_id": review.product_id
        })
        raise HTTPException(status_code=404, detail="Product not found for this review")

    # 将评价事件异步发送到Kafka (Kafka)
    await kafka_producer.send_review_to_kafka(review)
    logger.info("Review accepted and sent to Kafka", extra={
        "event": "review_sent_to_kafka",
        "product_id": review.product_id,
        "user_id": review.user_id
    })
    return {"message": "Review submission accepted."}


@app.post("/users/", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    logger.info("Creating user", extra={
        "event": "create_user",
        "user_email": user.email
    })
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        logger.warning("Email already registered", extra={
            "event": "email_already_registered",
            "user_email": user.email
        })
        raise HTTPException(status_code=400, detail="Email already registered")
    
    created_user = crud.create_user(db=db, user=user)
    logger.info("User created successfully", extra={
        "event": "user_created",
        "user_id": created_user.id,
        "user_email": created_user.email
    })
    return created_user


@app.get("/users/", response_model=list[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    logger.info("Fetching users list", extra={
        "event": "read_users",
        "skip": skip,
        "limit": limit
    })
    users = crud.get_users(db, skip=skip, limit=limit)
    logger.info("Users list fetched", extra={
        "event": "users_fetched",
        "count": len(users),
        "skip": skip,
        "limit": limit
    })
    return users


@app.get("/users/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    logger.info("Fetching user", extra={
        "event": "read_user",
        "user_id": user_id
    })
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        logger.warning("User not found", extra={
            "event": "user_not_found",
            "user_id": user_id
        })
        raise HTTPException(status_code=404, detail="User not found")
    
    logger.info("User found", extra={
        "event": "user_found",
        "user_id": user_id
    })
    return db_user


@app.put("/users/{user_id}", response_model=schemas.User)
def update_user(user_id: int, user_update: schemas.UserUpdate, db: Session = Depends(get_db)):
    logger.info("Updating user", extra={
        "event": "update_user",
        "user_id": user_id
    })
    db_user = crud.update_user(db, user_id=user_id, user_update=user_update)
    if db_user is None:
        logger.warning("User not found for update", extra={
            "event": "user_not_found_for_update",
            "user_id": user_id
        })
        raise HTTPException(status_code=404, detail="User not found")
    
    logger.info("User updated successfully", extra={
        "event": "user_updated",
        "user_id": user_id
    })
    return db_user


@app.delete("/users/{user_id}", status_code=status.HTTP_200_OK)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    logger.info("Deleting user", extra={
        "event": "delete_user",
        "user_id": user_id
    })
    if not crud.delete_user(db, user_id=user_id):
        logger.warning("User not found for deletion", extra={
            "event": "user_not_found_for_deletion",
            "user_id": user_id
        })
        raise HTTPException(status_code=404, detail="User not found")
    
    logger.info("User deleted successfully", extra={
        "event": "user_deleted",
        "user_id": user_id
    })
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














































































































































