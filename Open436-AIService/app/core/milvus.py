"""
Milvus向量数据库连接管理
"""
import logging
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility

from app.config import settings

logger = logging.getLogger(__name__)

COLLECTION_NAME = 'document_vectors'
VECTOR_DIM = 768


def connect_milvus():
    """连接Milvus"""
    try:
        connections.connect(
            alias='default',
            host=settings.MILVUS_HOST,
            port=settings.MILVUS_PORT,
        )
        logger.info(f'已连接Milvus: {settings.MILVUS_HOST}:{settings.MILVUS_PORT}')
    except Exception as e:
        logger.warning(f'Milvus连接失败（非致命）: {e}')


def init_vector_collection():
    """初始化向量集合"""
    try:
        if utility.has_collection(COLLECTION_NAME):
            logger.info(f'向量集合 {COLLECTION_NAME} 已存在')
            return

        fields = [
            FieldSchema(name='id', dtype=DataType.VARCHAR, max_length=36, is_primary=True),
            FieldSchema(name='document_id', dtype=DataType.VARCHAR, max_length=36),
            FieldSchema(name='chunk_index', dtype=DataType.INT64),
            FieldSchema(name='chunk_text', dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name='vector', dtype=DataType.FLOAT_VECTOR, dim=VECTOR_DIM),
        ]
        schema = CollectionSchema(fields, description='文档向量集合')
        collection = Collection(COLLECTION_NAME, schema)

        # 创建索引
        index_params = {
            'index_type': 'IVF_FLAT',
            'metric_type': 'COSINE',
            'params': {'nlist': 1024},
        }
        collection.create_index('vector', index_params)
        logger.info(f'向量集合 {COLLECTION_NAME} 创建成功')
    except Exception as e:
        logger.warning(f'向量集合初始化失败（非致命）: {e}')


def get_collection() -> Collection:
    """获取向量集合"""
    return Collection(COLLECTION_NAME)
