# app/config.py
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # PostgreSQL
    DATABASE_USER: str = os.getenv("DATABASE_USER", "default")
    DATABASE_PASSWORD: str = os.getenv("DATABASE_PASSWORD", "default")
    DATABASE_HOST: str = os.getenv("DATABASE_HOST", "localhost")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "mydatabase")

    # Redis
    REDIS_HOST: str = "redis-service"
    REDIS_PORT: int = 6379

    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka-service:9092"
    KAFKA_REVIEW_TOPIC: str = "product_reviews"

    # Elasticsearch
    ELASTICSEARCH_HOST: str = "elasticsearch-master:9200"  # Helm chart中es service的默认名字

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}@{self.DATABASE_HOST}/{self.DATABASE_NAME}"


settings = Settings()