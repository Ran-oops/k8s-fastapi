# 1. Standard Library Imports
import logging.config
from contextlib import asynccontextmanager
from typing import List

# 2. Third-Party Library Imports
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from prometheus_fastapi_instrumentator import Instrumentator
from asgi_correlation_id.middleware import CorrelationIdMiddleware

# 3. Local Application/Library Imports
from . import crud, schemas
from .database import get_db, create_db_and_tables
from .services import kafka_producer, redis_service, es_service
from .middlewares import log_and_monitor_middleware  # 导入整合后的中间件

# --- 日志配置 (ELK & JSON friendly) ---
# 确保日志格式为JSON，以便Logstash/Elasticsearch高效处理
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
        # 将根logger设置为处理JSON，以便所有模块的日志都遵循此格式
        "": {"handlers": ["json"], "level": "INFO"},
    },
}
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)


# --- Lifespan 管理器 (处理应用启动和关闭事件) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    管理应用的生命周期事件。
    - 启动时：创建数据库表，启动Kafka生产者。
    - 关闭时：优雅地关闭Kafka生产者。
    """
    # 在应用启动时运行
    logger.info("Application startup...")
    create_db_and_tables()
    logger.info("Database tables checked/created.")
    logger.info("Starting up Kafka producer...")

    # 新增：检查并创建Elasticsearch索引
    await es_service.create_index_if_not_exists()
    logger.info("Elasticsearch index checked/created.")

    await kafka_producer.producer.start()

    yield

    # 在应用关闭时运行
    logger.info("Application shutdown...")
    logger.info("Shutting down Kafka producer...")
    await kafka_producer.producer.stop()


# --- 创建FastAPI应用实例并注册生命周期事件 ---
app = FastAPI(
    title="Product Review System",
    description="A comprehensive example of a FastAPI application with microservices architecture components.",
    version="1.0.0",
    lifespan=lifespan
)

# --- 中间件注册 (Middleware Registration) ---
# 注册中间件的顺序非常重要，因为它们是按顺序处理请求的（洋葱模型）

# 1. (最外层) CorrelationIdMiddleware: 确保每个请求都有一个唯一的ID，用于全链路追踪
app.add_middleware(CorrelationIdMiddleware)

# 2. 自定义中间件: 记录丰富的请求/响应日志，并暴露自定义Prometheus指标
app.middleware("http")(log_and_monitor_middleware)

# 3. Prometheus Instrumentator: 自动暴露标准的FastAPI性能指标，并创建 /metrics 端点
Instrumentator().instrument(app).expose(app)



@app.get("/health", status_code=status.HTTP_200_OK, tags=["Health"])
def health_check():
    """Simple health check endpoint."""
    return {"status": "ok"}
# --- API Endpoints: Products ---

@app.post("/products/", response_model=schemas.Product, tags=["Products"])
def create_product(product: schemas.ProductCreate, db: Session = Depends(get_db)):
    """创建一个新商品。"""
    logger.info(f"Received request to create product with name: {product.name}")
    return crud.create_product(db=db, product=product)


@app.get("/products/{product_id}", response_model=schemas.Product, tags=["Products"])
def read_product(product_id: int, db: Session = Depends(get_db)):
    """
    根据ID获取单个商品。
    这个端点演示了缓存读取（Cache-aside）模式。
    """
    logger.info(f"Attempting to read product", extra={"product_id": product_id})

    # 1. 检查Redis缓存
    cached_product = redis_service.get_cached_product(product_id)
    if cached_product:
        logger.info("Product found in cache", extra={"product_id": product_id, "cache_hit": True})
        return cached_product

    logger.info("Product not in cache, querying database", extra={"product_id": product_id, "cache_hit": False})

    # 2. 如果缓存未命中，查询数据库
    db_product = crud.get_product(db, product_id=product_id)
    if db_product is None:
        logger.warning("Product not found in database", extra={"product_id": product_id})
        raise HTTPException(status_code=404, detail="Product not found")

    # 3. 将结果写入缓存
    redis_service.set_cached_product(db_product)
    logger.info("Product retrieved from database and cached", extra={"product_id": product_id})
    return db_product


@app.put("/products/{product_id}", response_model=schemas.Product, tags=["Products"])
def update_product_endpoint(product_id: int, product_update: schemas.ProductUpdate, db: Session = Depends(get_db)):
    """
    更新一个已存在的商品信息。
    这是一个部分更新，你只需要提供想要修改的字段。
    """
    logger.info(f"Received request to update product",
                extra={"product_id": product_id, "update_data": product_update.model_dump(exclude_unset=True)})

    updated_product = crud.update_product(db=db, product_id=product_id, product_update=product_update)

    if updated_product is None:
        logger.warning("Attempted to update a non-existent product", extra={"product_id": product_id})
        raise HTTPException(status_code=404, detail="Product not found")

    logger.info("Product updated successfully", extra={"product_id": product_id})
    return updated_product


@app.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Products"])
def delete_product_endpoint(product_id: int, db: Session = Depends(get_db)):
    """
    删除一个商品。
    成功后返回 204 No Content。
    """
    logger.info(f"Received request to delete product", extra={"product_id": product_id})

    success = crud.delete_product(db=db, product_id=product_id)

    if not success:
        logger.warning("Attempted to delete a non-existent product", extra={"product_id": product_id})
        raise HTTPException(status_code=404, detail="Product not found")

    logger.info("Product deleted successfully", extra={"product_id": product_id})
    # 对于 DELETE 操作，成功后通常不返回任何响应体
    return


@app.get("/products/search/", response_model=List[schemas.ProductSearchResult], tags=["Products"])
async def search_products_endpoint(q: str, db: Session = Depends(get_db)):
    """
    通过关键词全文搜索商品。

    - **q**: 搜索查询字符串
    """
    logger.info(f"Received search request with query: '{q}'")

    # 1. 在Elasticsearch中执行搜索
    search_results = await es_service.search_products(q)

    if not search_results:
        return []

    # 2. 从搜索结果中提取product_id
    product_ids = [result['product_id'] for result in search_results]

    # 3. 根据ID列表，一次性从PostgreSQL中批量获取完整的商品信息
    # 这是为了确保返回给用户的数据是最新、最完整的（"事实之源"）
    products = crud.get_products_by_ids(db, product_ids=product_ids)

    # (可选) 按ES返回的顺序对结果进行排序
    product_map = {product.id: product for product in products}
    sorted_products = [product_map[pid] for pid in product_ids if pid in product_map]

    return sorted_products



# --- API Endpoints: Reviews ---

@app.post("/reviews/", status_code=status.HTTP_202_ACCEPTED, tags=["Reviews"])
async def submit_review(review: schemas.ReviewCreate, db: Session = Depends(get_db)):
    """
    提交一个商品评价。
    这个端点是异步的，它将评价事件快速发送到Kafka，然后立即返回，实现了削峰填谷。
    """
    # 检查商品是否存在，这是一个快速的同步操作
    db_product = crud.get_product(db, product_id=review.product_id)
    if db_product is None:
        logger.warning("Attempted to submit review for a non-existent product", extra={"product_id": review.product_id})
        raise HTTPException(status_code=404, detail="Product not found for this review")

    # 将评价事件异步发送到Kafka
    await kafka_producer.send_review_to_kafka(review)
    logger.info(
        "Review submission accepted and sent to Kafka",
        extra={
            "product_id": review.product_id,
            "user_id": review.user_id,
            "rating": review.rating,
        }
    )
    return {"message": "Review submission accepted and is being processed."}


# --- API Endpoints: Users (CRUD) ---

@app.post("/users/", response_model=schemas.User, status_code=status.HTTP_201_CREATED, tags=["Users"])
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """创建一个新用户。"""
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        logger.warning("Attempted to create user with an already registered email", extra={"email": user.email})
        raise HTTPException(status_code=400, detail="Email already registered")
    logger.info("Creating a new user", extra={"email": user.email})
    return crud.create_user(db=db, user=user)


@app.get("/users/", response_model=List[schemas.User], tags=["Users"])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """获取用户列表。"""
    users = crud.get_users(db, skip=skip, limit=limit)
    return users


@app.get("/users/{user_id}", response_model=schemas.User, tags=["Users"])
def read_user(user_id: int, db: Session = Depends(get_db)):
    """根据ID获取单个用户。"""
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.put("/users/{user_id}", response_model=schemas.User, tags=["Users"])
def update_user(user_id: int, user_update: schemas.UserUpdate, db: Session = Depends(get_db)):
    """更新用户信息。"""
    db_user = crud.update_user(db, user_id=user_id, user_update=user_update)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    logger.info("User information updated", extra={"user_id": user_id})
    return db_user


@app.delete("/users/{user_id}", status_code=status.HTTP_200_OK, tags=["Users"])
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """删除一个用户。"""
    if not crud.delete_user(db, user_id=user_id):
        raise HTTPException(status_code=404, detail="User not found")
    logger.info("User deleted successfully", extra={"user_id": user_id})
    return {"detail": "User deleted successfully"}