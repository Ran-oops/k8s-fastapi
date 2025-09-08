# app/services/kafka_producer.py

from aiokafka import AIOKafkaProducer
import json
from ..config import settings
from .. import schemas
from typing import Union

# 1. 在模块顶层，只声明变量，不实例化
producer: Union[AIOKafkaProducer, None] = None


async def startup_kafka_producer():
    """
    在应用启动时被调用，实例化并启动Kafka生产者。
    """
    global producer
    # 2. 在异步函数内部进行实例化
    print("Initializing Kafka Producer...")
    producer = AIOKafkaProducer(bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS)
    await producer.start()
    print("Kafka Producer started.")


async def shutdown_kafka_producer():
    """
    在应用关闭时被调用，关闭Kafka生产者。
    """
    global producer
    if producer:
        print("Stopping Kafka Producer...")
        await producer.stop()
        print("Kafka Producer stopped.")


async def send_review_to_kafka(review: schemas.ReviewCreate):
    """将评价事件发送到Kafka"""
    global producer
    if producer is None:
        raise RuntimeError("Kafka producer is not initialized. Call startup_kafka_producer first.")

    event_data = {
        "product_id": review.product_id,
        "user_id": review.user_id,
        "rating": review.rating,
        "comment": review.comment
    }
    await producer.send_and_wait(
        settings.KAFKA_REVIEW_TOPIC,
        json.dumps(event_data).encode("utf-8")
    )