# app/services/kafka_producer.py
import logging
import json
from aiokafka import AIOKafkaProducer
from ..config import settings
from .. import schemas

logger = logging.getLogger(__name__)
producer = AIOKafkaProducer(bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS)

async def send_review_to_kafka(review: schemas.ReviewCreate):
    """将评价事件发送到Kafka"""
    event_data = {
        "product_id": review.product_id,
        "user_id": review.user_id,
        "rating": review.rating,
        "comment": review.comment
    }
    
    logger.info("Sending review to Kafka", extra={
        "event": "sending_review_to_kafka",
        "product_id": review.product_id,
        "user_id": review.user_id,
        "rating": review.rating
    })
    
    await producer.send_and_wait(
        settings.KAFKA_REVIEW_TOPIC,
        json.dumps(event_data).encode("utf-8")
    )
    
    logger.info("Review sent to Kafka successfully", extra={
        "event": "review_sent_to_kafka",
        "product_id": review.product_id,
        "user_id": review.user_id
    })