# app/services/kafka_producer.py
from aiokafka import AIOKafkaProducer
import json
from ..config import settings
from .. import schemas

producer = AIOKafkaProducer(bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS)

async def send_review_to_kafka(review: schemas.ReviewCreate):
    """将评价事件发送到Kafka"""
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