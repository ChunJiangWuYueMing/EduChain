"""
extractor.py — 文本提取器

从不同格式的文件中提取纯文本，供 SimHash 和 SHA-256 计算使用。
支持格式: .txt, .md, .pdf, .docx, .pptx
"""

import os
from pathlib import Path
from typing import Optional


def extract_text(file_path: str) -> str:
    """
    根据文件扩展名自动选择提取方式。

    Args:
        file_path: 文件路径

    Returns:
        提取的纯文本内容

    Raises:
        ValueError: 不支持的文件格式
        FileNotFoundError: 文件不存在
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")

    ext = path.suffix.lower()

    extractors = {
        ".txt": _extract_txt,
        ".md": _extract_txt,
        ".pdf": _extract_pdf,
        ".docx": _extract_docx,
        ".pptx": _extract_pptx,
    }

    extractor = extractors.get(ext)
    if extractor is None:
        raise ValueError(f"不支持的文件格式: {ext}（支持: {', '.join(extractors.keys())}）")

    text = extractor(file_path)

    # 统一清理：去除多余空白行，保留单个换行
    lines = [line.strip() for line in text.splitlines()]
    cleaned = "\n".join(line for line in lines if line)

    return cleaned


def _extract_txt(file_path: str) -> str:
    """提取纯文本 / Markdown 文件"""
    # 尝试多种编码
    for encoding in ("utf-8", "gbk", "gb2312", "latin-1"):
        try:
            with open(file_path, "r", encoding=encoding) as f:
                return f.read()
        except (UnicodeDecodeError, LookupError):
            continue
    # 最后用 errors=replace 兜底
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def _extract_pdf(file_path: str) -> str:
    """提取 PDF 文本"""
    try:
        from PyPDF2 import PdfReader
    except ImportError:
        raise ImportError("需要安装 PyPDF2: pip install PyPDF2")

    reader = PdfReader(file_path)
    pages_text = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages_text.append(text)

    return "\n".join(pages_text)


def _extract_docx(file_path: str) -> str:
    """提取 Word 文档文本"""
    try:
        from docx import Document
    except ImportError:
        raise ImportError("需要安装 python-docx: pip install python-docx")

    doc = Document(file_path)
    paragraphs = []

    # 提取正文段落
    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            paragraphs.append(text)

    # 提取表格内容
    for table in doc.tables:
        for row in table.rows:
            row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
            if row_text:
                paragraphs.append(row_text)

    return "\n".join(paragraphs)


def _extract_pptx(file_path: str) -> str:
    """提取 PowerPoint 文本"""
    try:
        from pptx import Presentation
    except ImportError:
        raise ImportError("需要安装 python-pptx: pip install python-pptx")

    prs = Presentation(file_path)
    slides_text = []

    for i, slide in enumerate(prs.slides, 1):
        texts = []
        for shape in slide.shapes:
            if shape.has_text_frame:
                for para in shape.text_frame.paragraphs:
                    text = para.text.strip()
                    if text:
                        texts.append(text)
            # 提取表格
            if shape.has_table:
                for row in shape.table.rows:
                    row_text = " | ".join(
                        cell.text.strip() for cell in row.cells if cell.text.strip()
                    )
                    if row_text:
                        texts.append(row_text)
        if texts:
            slides_text.append("\n".join(texts))

    return "\n".join(slides_text)
