# app/services/es_service.py

from elasticsearch import AsyncElasticsearch, NotFoundError
from ..config import settings
from .. import schemas

# 创建一个可复用的ES客户端实例
es_client = AsyncElasticsearch(
    hosts=[settings.ELASTICSEARCH_URL]
)

INDEX_NAME = "products"

async def create_index_if_not_exists():
    """在应用启动时检查并创建索引（如果不存在）"""
    if not await es_client.indices.exists(index=INDEX_NAME):
        print(f"Creating Elasticsearch index: {INDEX_NAME}")
        await es_client.indices.create(index=INDEX_NAME)

async def index_product(product: schemas.Product):
    """
    在Elasticsearch中为商品创建或更新文档。
    文档ID将与PostgreSQL中的商品ID保持一致。
    """
    document = {
        "product_id": product.id,
        "name": product.name,
        "description": product.description
    }
    await es_client.index(
        index=INDEX_NAME,
        id=str(product.id), # ES的文档ID必须是字符串
        document=document
    )
    print(f"Indexed product {product.id} in Elasticsearch.")

async def delete_product_from_index(product_id: int):
    """从Elasticsearch中删除商品文档"""
    try:
        await es_client.delete(index=INDEX_NAME, id=str(product_id))
        print(f"Deleted product {product_id} from Elasticsearch.")
    except NotFoundError:
        print(f"Product {product_id} not found in Elasticsearch for deletion.")
        pass

async def search_products(query: str) -> list[dict]:
    """
    根据关键词在Elasticsearch中搜索商品。
    """
    try:
        response = await es_client.search(
            index=INDEX_NAME,
            query={
                "multi_match": {
                    "query": query,
                    "fields": ["name", "description"], # 在名称和描述字段中搜索
                    "fuzziness": "AUTO" # 启用模糊匹配，容忍轻微的拼写错误
                }
            }
        )
        return [hit['_source'] for hit in response['hits']['hits']]
    except Exception as e:
        print(f"Error during Elasticsearch search: {e}")
        return []