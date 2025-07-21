import json
from pathlib import Path
from typing import List, Dict, Optional


class ChunkedDataLoader:
    def __init__(self, chunked_dir="data/chunked_legal_data"):
        self.chunked_dir = Path(chunked_dir)
        self._chunks = None

    def load_all_chunks(self) -> List[Dict]:
        """Load all chunks from JSON files"""
        if self._chunks is None:
            self._chunks = []

            for json_file in self.chunked_dir.glob("*.json"):
                with open(json_file, "r", encoding="utf-8") as f:
                    chunks = json.load(f)
                    self._chunks.extend(chunks)

        return self._chunks

    def search_chunks(
        self, query_embedding: List[float], threshold: float = 0.78, limit: int = 5
    ) -> List[Dict]:
        """Search chunks using embedding similarity"""
        chunks = self.load_all_chunks()

        # Calculate similarity for each chunk
        chunk_similarities = []
        for chunk in chunks:
            if "embedding" in chunk:
                # Calculate cosine similarity
                similarity = self._cosine_similarity(
                    query_embedding, chunk["embedding"]
                )
                if similarity >= threshold:
                    chunk_similarities.append(
                        {"chunk": chunk, "similarity": similarity}
                    )

        # Sort by similarity (highest first) and return top results
        chunk_similarities.sort(key=lambda x: x["similarity"], reverse=True)
        return [item["chunk"] for item in chunk_similarities[:limit]]

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        import math

        # Calculate dot product
        dot_product = sum(a * b for a, b in zip(vec1, vec2))

        # Calculate magnitudes
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(a * a for a in vec2))

        # Avoid division by zero
        if magnitude1 == 0 or magnitude2 == 0:
            return 0

        return dot_product / (magnitude1 * magnitude2)

    def get_chunk_by_id(self, chunk_id: str) -> Optional[Dict]:
        """Get specific chunk by ID"""
        chunks = self.load_all_chunks()
        return next((chunk for chunk in chunks if chunk["id"] == chunk_id), None)
