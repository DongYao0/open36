"""
文档处理工具 - PyMuPDF解析 + Milvus向量存储
"""
import logging
import uuid

from langchain_core.tools import tool

logger = logging.getLogger(__name__)


@tool
def parse_pdf(file_path: str) -> str:
    """
    解析PDF文档，提取纯文本内容。

    Args:
        file_path: PDF文件路径
    """
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(file_path)
        text = ''
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    except Exception as e:
        logger.error(f'PDF解析失败: {e}')
        return f'PDF解析失败: {str(e)}'


@tool
def split_chunks(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
    """
    将文本分段，用于向量化存储。

    Args:
        text: 原始文本
        chunk_size: 每段最大字符数，默认1000
        overlap: 段间重叠字符数，默认200
    """
    if not text:
        return []

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk.strip())
        start = end - overlap
        if start >= len(text):
            break
    return chunks


@tool
def store_vectors(document_id: str, chunks: list[str]) -> dict:
    """
    将文本分段生成向量并存入Milvus。

    Args:
        document_id: 文档ID
        chunks: 文本分段列表
    """
    try:
        from pymilvus import Collection
        from app.core.milvus import get_collection, VECTOR_DIM
        import random

        collection = get_collection()
        ids = []
        doc_ids = []
        chunk_indices = []
        chunk_texts = []
        vectors = []

        for i, chunk in enumerate(chunks):
            # 生成模拟向量（实际应调用Embedding模型）
            vector = [random.random() for _ in range(VECTOR_DIM)]

            chunk_id = str(uuid.uuid4())
            ids.append(chunk_id)
            doc_ids.append(document_id)
            chunk_indices.append(i)
            chunk_texts.append(chunk[:65535])  # Milvus VARCHAR限制
            vectors.append(vector)

        collection.insert([ids, doc_ids, chunk_indices, chunk_texts, vectors])
        collection.flush()

        return {'stored': len(chunks), 'document_id': document_id}
    except Exception as e:
        logger.error(f'向量存储失败: {e}')
        return {'error': str(e)}


@tool
def search_similar(query: str, top_k: int = 5) -> list[dict]:
    """
    在Milvus中进行相似度检索。

    Args:
        query: 查询文本
        top_k: 返回最相似的N条记录，默认5
    """
    try:
        from pymilvus import Collection
        from app.core.milvus import get_collection, VECTOR_DIM
        import random

        collection = get_collection()
        collection.load()

        # 生成查询向量（实际应调用Embedding模型）
        query_vector = [random.random() for _ in range(VECTOR_DIM)]

        results = collection.search(
            data=[query_vector],
            anns_field='vector',
            param={'metric_type': 'COSINE', 'params': {'nprobe': 16}},
            limit=top_k,
            output_fields=['document_id', 'chunk_index', 'chunk_text'],
        )

        hits = []
        for hit in results[0]:
            hits.append({
                'id': hit.id,
                'score': hit.score,
                'document_id': hit.entity.get('document_id'),
                'chunk_index': hit.entity.get('chunk_index'),
                'chunk_text': hit.entity.get('chunk_text', '')[:500],
            })
        return hits
    except Exception as e:
        logger.error(f'向量检索失败: {e}')
        return [{'error': str(e)}]
