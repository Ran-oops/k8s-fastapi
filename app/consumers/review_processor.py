# app/consumers/review_processor.py
import asyncio
import json
import logging
from aiokafka import AIOKafkaConsumer
from sqlalchemy.orm import sessionmaker
from ..config import settings
from .. import crud, models, schemas, database
from ..services.prometheus_metrics import REVIEWS_PROCESSED_COUNTER

logger = logging.getLogger(__name__)

async def consume_reviews():
    consumer = AIOKafkaConsumer(
        settings.KAFKA_REVIEW_TOPIC,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id="review_processor_group"  # 消费者组ID
    )
    await consumer.start()
    logger.info("Consumer started...", extra={"event": "consumer_started", "service": "review_processor"})

    # 创建一个独立的数据库会话
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=database.engine)
    db = SessionLocal()

    try:
        async for msg in consumer:
            logger.info("Message received from Kafka", extra={
                "event": "kafka_message_received",
                "topic": msg.topic,
                "partition": msg.partition,
                "offset": msg.offset
            })
            
            review_data = json.loads(msg.value.decode('utf-8'))
            logger.info("Processing review data", extra={
                "event": "processing_review",
                "product_id": review_data.get("product_id"),
                "user_id": review_data.get("user_id"),
                "rating": review_data.get("rating")
            })

            # 创建Pydantic模型用于验证
            review_to_create = schemas.ReviewCreate(**review_data)

            # 将评价写入PostgreSQL
            db_review = crud.create_review(db=db, review=review_to_create)
            logger.info("Review saved to DB", extra={
                "event": "review_saved_to_db",
                "review_id": db_review.id,
                "product_id": review_to_create.product_id,
                "user_id": review_to_create.user_id
            })

            # 更新自定义Prometheus指标
            REVIEWS_PROCESSED_COUNTER.inc()
            logger.info("Review processed successfully", extra={
                "event": "review_processed",
                "review_id": db_review.id
            })

            # 在这里，你还可以添加逻辑来更新Elasticsearch中的商品文档
            # (例如：更新商品的平均评分)

    except Exception as e:
        logger.error("Error processing message", extra={
            "event": "processing_error",
            "error": str(e)
        })
    finally:
        await consumer.stop()
        db.close()
        logger.info("Consumer stopped.", extra={"event": "consumer_stopped", "service": "review_processor"})


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(consume_reviews())