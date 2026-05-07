import uuid
import tiktoken
from pathlib import Path
from typing import Optional
import fitz
from docx import Document


def chunk_document(file_path: str) -> list[dict]:
    file_ext = Path(file_path).suffix.lower()

    if file_ext == ".pdf":
        text_blocks = _extract_pdf(file_path)
    elif file_ext == ".docx":
        text_blocks = _extract_docx(file_path)
    elif file_ext == ".txt":
        text_blocks = _extract_txt(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_ext}")

    filename = Path(file_path).name
    encoding = tiktoken.get_encoding("cl100k_base")

    chunks = []
    for block_text, position_info in text_blocks:
        tokens = encoding.encode(block_text)

        for i in range(0, len(tokens), 500):
            chunk_tokens = tokens[i : i + 500]
            chunk_text = tiktoken.get_encoding("cl100k_base").decode(chunk_tokens)

            chunks.append(
                {
                    "chunk_id": str(uuid.uuid4()),
                    "text": chunk_text,
                    "source_file": filename,
                    "page_number": position_info.get("page_number"),
                    "char_count": len(chunk_text),
                }
            )

    return chunks


def _extract_pdf(file_path: str) -> list[tuple[str, dict]]:
    doc = fitz.open(file_path)
    text_blocks = []

    for page_num, page in enumerate(doc, 1):
        text = page.get_text()
        if text.strip():
            text_blocks.append((text, {"page_number": page_num}))

    doc.close()
    return text_blocks


def _extract_docx(file_path: str) -> list[tuple[str, dict]]:
    doc = Document(file_path)
    text_blocks = []

    for para_idx, paragraph in enumerate(doc.paragraphs, 1):
        text = paragraph.text
        if text.strip():
            text_blocks.append((text, {"page_number": para_idx}))

    return text_blocks


def _extract_txt(file_path: str) -> list[tuple[str, dict]]:
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()

    return [(text, {"page_number": 1})]
