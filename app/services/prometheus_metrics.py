# app/services/prometheus_metrics.py
from prometheus_client import Counter

# 创建一个自定义指标：已处理的评价总数
REVIEWS_PROCESSED_COUNTER = Counter(
    "reviews_processed_total",
    "Total number of product reviews processed by the consumer."
)