"""
文件上传接口 - 支持 PDF/TXT/代码文件
"""
import logging
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, UploadFile, File
from fastapi.responses import JSONResponse

from app.dependencies import get_current_admin
from app.core.responses import success_response, error_response

logger = logging.getLogger(__name__)
router = APIRouter()

# 上传配置
UPLOAD_DIR = Path(__file__).parent.parent.parent / 'uploads'
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {'.pdf', '.txt', '.md', '.csv', '.json', '.py', '.js', '.java', '.c', '.cpp', '.h', '.hpp', '.go', '.rs', '.ts'}

# 确保上传目录存在
UPLOAD_DIR.mkdir(exist_ok=True)


def _extract_text(file_path: Path, suffix: str) -> str:
    """从文件中提取文本内容"""
    try:
        if suffix == '.pdf':
            import fitz
            doc = fitz.open(str(file_path))
            text_parts = []
            for page in doc:
                text_parts.append(page.get_text())
            doc.close()
            return '\n'.join(text_parts)
        else:
            # 文本文件直接读取
            return file_path.read_text(encoding='utf-8', errors='ignore')
    except Exception as e:
        logger.warning(f'文件文本提取失败: {e}')
        return ''


@router.post('/upload')
async def upload_file(
    file: UploadFile = File(...),
    user_id: int = Depends(get_current_admin),
):
    """
    上传文件并提取文本内容

    支持: PDF, TXT, MD, CSV, JSON, 代码文件
    限制: 10MB
    """
    # 验证文件扩展名
    suffix = Path(file.filename or '').suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        resp, code = error_response(
            f'不支持的文件类型: {suffix}，支持: {", ".join(sorted(ALLOWED_EXTENSIONS))}',
            code=40001, status_code=400,
        )
        return JSONResponse(content=resp, status_code=code)

    # 读取文件内容
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        resp, code = error_response(
            f'文件大小超过限制 ({MAX_FILE_SIZE // 1024 // 1024}MB)',
            code=40002, status_code=400,
        )
        return JSONResponse(content=resp, status_code=code)

    # 保存文件
    file_id = str(uuid.uuid4())
    save_path = UPLOAD_DIR / f'{file_id}{suffix}'
    save_path.write_bytes(content)

    # 提取文本
    text = _extract_text(save_path, suffix)
    # 截断过长的文本（避免传给 LLM 时超 token）
    if len(text) > 10000:
        text = text[:10000] + '\n\n... [文本过长，已截断]'

    logger.info(f'文件上传成功: {file.filename} ({len(content)} bytes) -> {file_id}')

    return JSONResponse(content=success_response(data={
        'file_id': file_id,
        'filename': file.filename,
        'size': len(content),
        'text': text,
    }))
