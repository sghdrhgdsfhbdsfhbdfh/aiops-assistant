"""文件上传接口模块"""

from pathlib import Path

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from fastapi.responses import JSONResponse
from loguru import logger

from app.config import config
from app.services.vector_index_service import vector_index_service
from app.utils.uploads import (
    build_non_conflicting_path,
    ensure_path_within_directory,
    get_file_extension,
    parse_allowed_extensions,
    sanitize_filename,
)

router = APIRouter()

# 文件上传后存储的路径
UPLOAD_DIR = Path(config.upload_dir)
ALLOWED_EXTENSIONS = parse_allowed_extensions(config.upload_allowed_extensions)


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    上传文件并自动创建向量索引

    Args:
        file: 上传的文件

    Returns:
        JSONResponse: 上传结果
    """
    try:
        # 1. 验证文件
        if not file.filename:
            raise HTTPException(status_code=400, detail="文件名不能为空")

        # 2. 规范化文件名
        try:
            safe_filename = sanitize_filename(file.filename)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        # 3. 验证文件扩展名
        file_extension = get_file_extension(safe_filename)
        if file_extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件格式，仅支持: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
            )

        # 4. 创建上传目录
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        # 5. 保存文件
        file_path = build_non_conflicting_path(UPLOAD_DIR, safe_filename)

        # 读取并保存文件内容
        content = await file.read()

        # 验证文件大小
        if len(content) > config.upload_max_file_size:
            raise HTTPException(
                status_code=400,
                detail=f"文件大小超过限制（最大 {config.upload_max_file_size} 字节）",
            )

        try:
            content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise HTTPException(status_code=400, detail="仅支持 UTF-8 编码的文本文件") from exc

        file_path.write_bytes(content)

        logger.info(f"文件上传成功: {file_path}")

        # 5. 自动创建向量索引
        try:
            logger.info(f"开始为上传文件创建向量索引: {file_path}")
            vector_index_service.index_single_file(str(file_path))
            logger.info(f"向量索引创建成功: {file_path}")
        except Exception as e:
            logger.error(f"向量索引创建失败: {file_path}, 错误: {e}")
            # 注意：即使索引失败，文件上传仍然成功，只是记录错误日志

        # 6. 返回响应
        return JSONResponse(
            status_code=200,
            content={
                "code": 200,
                "message": "success",
                "data": {
                    "filename": safe_filename,
                    "file_path": str(file_path),
                    "size": len(content),
                },
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件上传失败: {e}")
        raise HTTPException(status_code=500, detail=f"文件上传失败: {e}")


@router.post("/index_directory")
async def index_directory(
    directory_path: str | None = Query(
        default=None,
        description="要索引的上传目录子路径；默认索引上传目录",
    ),
):
    """
    索引指定目录下的所有文件

    Args:
        directory_path: 目录路径（可选，默认使用 uploads 目录）

    Returns:
        JSONResponse: 索引结果
    """
    try:
        upload_root = UPLOAD_DIR.resolve()
        if directory_path:
            requested_path = Path(directory_path)
            if not requested_path.is_absolute():
                requested_path = upload_root / requested_path
            try:
                target_path = ensure_path_within_directory(requested_path, upload_root)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
        else:
            target_path = upload_root

        logger.info(f"开始索引目录: {target_path}")

        # 执行索引
        result = vector_index_service.index_directory(str(target_path))

        return JSONResponse(
            status_code=200,
            content={
                "code": 200,
                "message": "success" if result.success else "partial_success",
                "data": result.to_dict(),
            },
        )

    except Exception as e:
        logger.error(f"索引目录失败: {e}")
        raise HTTPException(status_code=500, detail=f"索引目录失败: {e}")
