# app/services/redis_service.py
import redis
import json
from ..config import settings
from .. import schemas

# 创建一个可复用的Redis连接池
redis_pool = redis.ConnectionPool(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0)

def get_redis_conn():
    return redis.Redis(connection_pool=redis_pool)

def get_cached_product(product_id: int):
    """从Redis缓存中获取商品信息"""
    r = get_redis_conn()
    product_data = r.get(f"product:{product_id}")
    if product_data:
        print(f"HIT CACHE for product {product_id}")
        return schemas.Product.model_validate(json.loads(product_data))
    print(f"MISS CACHE for product {product_id}")
    return None

def set_cached_product(product: schemas.Product):
    """将商品信息设置到Redis缓存，并设置10分钟过期"""
    r = get_redis_conn()
    product_json = product.model_dump_json()
    # PSETEX a key to expire in 10 minutes (600000 milliseconds)
    r.setex(f"product:{product.id}", 600 * 1000, product_json)
    print(f"SET CACHE for product {product.id}")