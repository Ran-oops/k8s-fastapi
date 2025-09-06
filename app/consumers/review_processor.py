# app/consumers/review_processor.py
import asyncio
import json
from aiokafka import AIOKafkaConsumer
from sqlalchemy.orm import sessionmaker
from ..config import settings
from .. import crud, models, schemas, database
from ..services.prometheus_metrics import REVIEWS_PROCESSED_COUNTER


async def consume_reviews():
    consumer = AIOKafkaConsumer(
        settings.KAFKA_REVIEW_TOPIC,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id="review_processor_group"  # 消费者组ID
    )
    await consumer.start()
    print("Consumer started...")

    # 创建一个独立的数据库会话
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=database.engine)
    db = SessionLocal()

    try:
        async for msg in consumer:
            print(f"Consumed message: {msg.value.decode('utf-8')}")
            review_data = json.loads(msg.value.decode('utf-8'))

            # 创建Pydantic模型用于验证
            review_to_create = schemas.ReviewCreate(**review_data)

            # 将评价写入PostgreSQL
            crud.create_review(db=db, review=review_to_create)
            print(f"Review for product {review_to_create.product_id} saved to DB.")

            # 更新自定义Prometheus指标
            REVIEWS_PROCESSED_COUNTER.inc()

            # 在这里，你还可以添加逻辑来更新Elasticsearch中的商品文档
            # (例如：更新商品的平均评分)

    finally:
        await consumer.stop()
        db.close()
        print("Consumer stopped.")


if __name__ == "__main__":
    asyncio.run(consume_reviews())