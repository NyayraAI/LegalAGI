import json
import re
from pathlib import Path
from datetime import datetime
import pdfplumber
from hashlib import md5
from markitdown import MarkItDown
from .metadata_extractor import MetadataExtractor
from utils.core.embed import embed_texts_batch


class PDFProcessor:
    def __init__(
        self, source_dir="data/raw_pdfs", output_dir="data/chunked_legal_data"
    ):
        self.source_dir = Path(source_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.extractor = MetadataExtractor()
        self.chunk_size = 1000
        self.markitdown = MarkItDown()

    def clean_text(self, text):
        """Basic text cleaning"""
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def chunk_markdown_text(self, markdown_text):
        """
        Chunk markdown text into meaningful sections based on headers and content.
        Returns chunks that maintain context and are suitable for embedding.
        """
        if not markdown_text.strip():
            return []

        # Debug: Print markdown preview
        print("MARKDOWN PREVIEW:", markdown_text[:1000])

        # Split by major headers (# and ##)
        sections = re.split(r"(^#{1,2}\s+.*$)", markdown_text, flags=re.MULTILINE)

        # Debug: Print number of sections found
        print("Number of sections found:", len(sections))

        chunks = []
        current_chunk = ""
        current_header = ""

        for section in sections:
            section = section.strip()
            if not section:
                continue

            # Check if this is a header
            if re.match(r"^#{1,2}\s+", section):
                # If we have accumulated content, save it as a chunk
                if current_chunk.strip():
                    chunks.append(self._finalize_chunk(current_header, current_chunk))

                # Start new chunk with this header
                current_header = section
                current_chunk = section + "\n\n"
            else:
                # This is content - add to current chunk
                potential_chunk = current_chunk + section + "\n\n"

                # Check if adding this content would exceed chunk size
                if self._count_words(potential_chunk) > self.chunk_size:
                    # Save current chunk if it has content
                    if (
                        current_chunk.strip()
                        and current_chunk != current_header + "\n\n"
                    ):
                        chunks.append(
                            self._finalize_chunk(current_header, current_chunk)
                        )

                    # Start new chunk with header and this content
                    current_chunk = current_header + "\n\n" + section + "\n\n"
                else:
                    current_chunk = potential_chunk

        # Add final chunk if there's content
        if current_chunk.strip():
            chunks.append(self._finalize_chunk(current_header, current_chunk))

        # If no chunks were created, return the original text as a single chunk
        if not chunks:
            chunks = [markdown_text]

        # Debug: Print number of chunks created
        print("Chunks created (header-based):", len(chunks))

        return chunks

    def _count_words(self, text):
        """Count words in text"""
        return len(text.split())

    def _finalize_chunk(self, header, content):
        """Clean and finalize a chunk"""
        chunk = content.strip()

        # Ensure chunk doesn't end with multiple newlines
        chunk = re.sub(r"\n{3,}", "\n\n", chunk)

        return chunk

    def chunk_by_paragraphs(self, markdown_text):
        """
        Alternative chunking method: chunk by paragraphs with size limits.
        Useful for documents without clear header structure.
        """
        if not markdown_text.strip():
            return []

        # Split by double newlines (paragraphs)
        paragraphs = [p.strip() for p in markdown_text.split("\n\n") if p.strip()]

        chunks = []
        current_chunk = ""

        for paragraph in paragraphs:
            potential_chunk = (
                current_chunk + ("\n\n" if current_chunk else "") + paragraph
            )

            if self._count_words(potential_chunk) > self.chunk_size:
                # Save current chunk if it has content
                if current_chunk:
                    chunks.append(current_chunk.strip())

                # Start new chunk with this paragraph
                current_chunk = paragraph
            else:
                current_chunk = potential_chunk

        # Add final chunk
        if current_chunk:
            chunks.append(current_chunk.strip())

        # Debug: Print number of chunks created by paragraph chunking
        print("Chunks created (paragraph-based):", len(chunks))

        # If still only one chunk and text is long, fallback to fixed-size word chunking
        if len(chunks) < 2 and self._count_words(markdown_text) > self.chunk_size:
            print("[INFO] Fallback: chunking by fixed word count")
            chunks = self.chunk_by_fixed_word_count(markdown_text)
            print("Chunks created (fixed-size):", len(chunks))

        return chunks if chunks else [markdown_text]

    def chunk_by_fixed_word_count(self, text):
        """
        Final fallback: split text into fixed-size word chunks.
        """
        words = text.split()
        chunks = []
        for i in range(0, len(words), self.chunk_size):
            chunk = " ".join(words[i : i + self.chunk_size])
            chunks.append(chunk)
        return chunks

    def process_pdf(self, pdf_path, force=False):
        filename = pdf_path.name
        json_filename = self.output_dir / f"{filename.replace('.pdf', '.json')}"

        if json_filename.exists() and not force:
            print(f"[SKIP] {filename} already processed")
            return

        try:
            # Extract metadata
            metadata = self.extractor.extract_from_filename(filename)

            # Convert PDF to markdown using markitdown
            try:
                # Use markitdown to convert PDF to markdown
                result = self.markitdown.convert(str(pdf_path))
                markdown_text = result.text_content

                # Fallback to pdfplumber if markitdown fails
                if not markdown_text or len(markdown_text.strip()) < 100:
                    print(
                        f"[WARN] MarkItDown produced minimal content for {filename}, falling back to pdfplumber"
                    )
                    markdown_text = self._extract_with_pdfplumber(pdf_path)

            except Exception as e:
                print(
                    f"[WARN] MarkItDown failed for {filename}: {e}, falling back to pdfplumber"
                )
                markdown_text = self._extract_with_pdfplumber(pdf_path)

            # Clean the markdown text
            markdown_text = self.clean_text(markdown_text)

            # Add content metadata
            content_metadata = self.extractor.extract_from_content(markdown_text)
            metadata.update(content_metadata)

            # Chunk the markdown text
            chunks = self.chunk_markdown_text(markdown_text)

            # If chunking produces very few chunks, try paragraph-based chunking
            if len(chunks) < 3 and len(markdown_text.split()) > self.chunk_size:
                chunks = self.chunk_by_paragraphs(markdown_text)

            # Create chunk documents
            chunked_docs = []
            for i, chunk in enumerate(chunks):
                chunked_docs.append(
                    {
                        "id": md5(chunk.encode()).hexdigest(),
                        "chunk_index": i,
                        "content": chunk,
                        "metadata": {
                            **metadata,
                            "collected_date": datetime.now().isoformat(),
                            "processing_method": "markitdown",
                            "chunk_type": "markdown",
                            "text_length": len(chunk),
                        },
                        "label": "positive",
                    }
                )

            # Save to JSON
            with open(json_filename, "w", encoding="utf-8") as f:
                json.dump(chunked_docs, f, indent=2, ensure_ascii=False)

            print(f"[OK] {filename} → {len(chunked_docs)} markdown chunks")
            # Generate embeddings
            texts = [doc["content"] for doc in chunked_docs]
            embed_texts_batch(
                texts=texts,
                chunks=chunked_docs,
                metadata={
                    "file_path": str(json_filename),
                    "chunk_count": len(chunked_docs),
                },
                store_results=True,
            )

            return chunked_docs

        except Exception as e:
            print(f"[ERR] Failed to process {filename}: {e}")

    def _extract_with_pdfplumber(self, pdf_path):
        """Fallback text extraction using pdfplumber"""
        with pdfplumber.open(pdf_path) as pdf:
            full_text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    full_text += page_text + "\n"
        return full_text

    def process_all_pdfs(self, force=False):
        """Process all PDFs in the source directory"""
        for pdf_file in self.source_dir.glob("*.pdf"):
            self.process_pdf(pdf_file, force=force)


# Test if running directly
if __name__ == "__main__":
    processor = PDFProcessor()
    processor.process_all_pdfs()

import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class PDFWatcher(FileSystemEventHandler):
    def __init__(self, processor):
        self.processor = processor

    def on_created(self, event):
        # Ensure event.src_path is a string and endswith receives a tuple as per lint
        if isinstance(event.src_path, str) and event.src_path.endswith((".pdf",)):
            print(f"New PDF detected: {event.src_path}")
            # Ensure Path receives a str, not bytes
            self.processor.process_pdf(Path(str(event.src_path)))


def start_watching(source_dir: str = "data/raw_pdfs"):
    processor = PDFProcessor()
    event_handler = PDFWatcher(processor)
    observer = Observer()
    observer.schedule(event_handler, source_dir, recursive=False)
    observer.start()
    print(f"Watching {source_dir} for new PDFs...")
    return observer
