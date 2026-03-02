import zipfile
from io import BytesIO
from loguru import logger


def extract_markdown_from_zip(zip_content: bytes) -> str:
    try:
        with zipfile.ZipFile(BytesIO(zip_content), "r") as zip_ref:
            for file_name in zip_ref.namelist():
                if file_name.endswith(".md"):
                    with zip_ref.open(file_name) as f:
                        md_content = f.read().decode("utf-8")
                        logger.info(f"从 ZIP 中提取 Markdown 成功: {file_name}")
                        return md_content
        logger.warning("ZIP 文件中未找到 Markdown 文件")
        return ""
    except Exception as e:
        logger.error(f"从 ZIP 提取 Markdown 失败: {str(e)}")
        raise
