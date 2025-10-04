import os
import tempfile
from pathlib import Path
from typing import List

import chainlit as cl

try:
    from pypdf import PdfReader  # type: ignore

    PDF_AVAILABLE = True
except Exception:
    PDF_AVAILABLE = False

try:
    from docx import Document  # type: ignore

    DOCX_AVAILABLE = True
except Exception:
    DOCX_AVAILABLE = False


def _read_bytes(file: cl.File) -> bytes:
    content = getattr(file, "content", None)
    if isinstance(content, (bytes, bytearray)):
        return bytes(content)
    path = getattr(file, "path", None)
    if isinstance(path, str) and path:
        with open(path, "rb") as fh:
            return fh.read()
    raise ValueError("Unable to read uploaded file bytes (no content or path)")


async def extract_documents_text(files: List[cl.File]) -> str:
    parts: List[str] = []
    for f in files:
        name = str(f.name)
        ext = Path(name).suffix.lower()
        try:
            if ext == ".pdf" and PDF_AVAILABLE:
                raw = _read_bytes(f)
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(raw)
                    p = tmp.name
                reader = PdfReader(p)  # type: ignore
                file_text: List[str] = []
                for i, page in enumerate(reader.pages, start=1):
                    t = (page.extract_text() or "").strip()
                    if t:
                        file_text.append(f"[Page {i}]\n{t}")
                os.unlink(p)
                if file_text:
                    parts.append(f"**{name}**\n" + "\n\n".join(file_text))
            elif ext in (".docx", ".doc") and DOCX_AVAILABLE:
                raw = _read_bytes(f)
                with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
                    tmp.write(raw)
                    p = tmp.name
                doc = Document(p)  # type: ignore
                text_lines = [
                    p.text.strip() for p in doc.paragraphs if p.text and p.text.strip()
                ]
                os.unlink(p)
                if text_lines:
                    parts.append(f"**{name}**\n" + "\n".join(text_lines))
            else:
                cl.logger.info(
                    f"Skipped document {name} (ext={ext}, available: PDF={PDF_AVAILABLE}, DOCX={DOCX_AVAILABLE})"
                )
        except Exception as e:  # defensive
            cl.logger.error(f"Error reading document {name}: {e}")
    return "\n\n".join(parts)
