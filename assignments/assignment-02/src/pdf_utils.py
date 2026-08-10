from pathlib import Path
from pypdf import PdfReader


def extract_pdf_text(pdf_path: str) -> str:
    path = Path(pdf_path)

    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    if path.suffix.lower() != ".pdf":
        raise ValueError(f"Expected a PDF file: {pdf_path}")

    try:
        reader = PdfReader(path)
        pages = []

        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text)

        full_text = "\n".join(pages).strip()

        if not full_text:
            raise ValueError(
                f"No readable text found in PDF: {pdf_path}"
            )

        return full_text

    except Exception as exc:
        raise RuntimeError(
            f"Failed to extract text from PDF '{pdf_path}': {exc}"
        ) from exc