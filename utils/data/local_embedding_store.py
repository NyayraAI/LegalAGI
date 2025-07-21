"""
Local file-based embedding storage for open source version
"""
import os
import json
import pickle
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from sklearn.metrics.pairwise import cosine_similarity

from .embedding_store import EmbeddingStore

class LocalEmbeddingStore(EmbeddingStore):
    """Local file-based embedding storage"""

    def __init__(self, config: Dict[str, Any]):
        self.storage_path = Path(config.get("path", "data/embeddings/"))
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # File paths
        self.embeddings_file = self.storage_path / "embeddings.pkl"
        self.chunks_file = self.storage_path / "chunks.json"
        self.metadata_file = self.storage_path / "metadata.json"

        # Load existing data
        self._load_data()

    def _load_data(self):
        """Load existing embeddings and chunks from files"""
        # Load embeddings
        if self.embeddings_file.exists():
            try:
                with open(self.embeddings_file, 'rb') as f:
                    self.embeddings = pickle.load(f)
            except Exception as e:
                print(f"Warning: Could not load embeddings: {e}")
                self.embeddings = []
        else:
            self.embeddings = []

        # Load chunks
        if self.chunks_file.exists():
            try:
                with open(self.chunks_file, 'r', encoding='utf-8') as f:
                    self.chunks = json.load(f)
            except Exception as e:
                print(f"Warning: Could not load chunks: {e}")
                self.chunks = []
        else:
            self.chunks = []

        # Load metadata
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
            except Exception as e:
                print(f"Warning: Could not load metadata: {e}")
                self.metadata = {}
        else:
            self.metadata = {}

    def _save_data(self):
        """Save embeddings and chunks to files"""
        try:
            # Save embeddings
            with open(self.embeddings_file, 'wb') as f:
                pickle.dump(self.embeddings, f)

            # Save chunks
            with open(self.chunks_file, 'w', encoding='utf-8') as f:
                json.dump(self.chunks, f, indent=2, ensure_ascii=False)

            # Save metadata
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2, ensure_ascii=False)

            return True
        except Exception as e:
            print(f"Error saving data: {e}")
            return False

    def store_embeddings(self, 
                        embeddings: List[np.ndarray], 
                        chunks: List[Dict[str, Any]], 
                        metadata: Dict[str, Any]) -> bool:
        """Store embeddings with associated chunks and metadata"""
        try:
            # Get file path for tracking
            file_path = metadata.get("file_path", "unknown")

            # Remove existing embeddings for this file
            if file_path in self.metadata:
                self._remove_file_embeddings(file_path)

            # Add new embeddings
            start_idx = len(self.embeddings)
            self.embeddings.extend(embeddings)

            # Add chunks with additional metadata
            for i, chunk in enumerate(chunks):
                chunk_with_meta = chunk.copy()
                chunk_with_meta.update({
                    "embedding_idx": start_idx + i,
                    "file_path": file_path,
                    "stored_at": datetime.now().isoformat()
                })
                self.chunks.append(chunk_with_meta)

            # Update metadata
            self.metadata[file_path] = {
                "chunk_count": len(chunks),
                "start_idx": start_idx,
                "end_idx": start_idx + len(chunks) - 1,
                "stored_at": datetime.now().isoformat(),
                **metadata
            }

            # Save to files
            return self._save_data()

        except Exception as e:
            print(f"Error storing embeddings: {e}")
            return False

    def search_embeddings(self, 
                         query_embedding: np.ndarray, 
                         top_k: int = 5, 
                         threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Search for similar embeddings"""
        if not self.embeddings:
            return []

        try:
            # Convert embeddings to numpy array
            embeddings_array = np.array(self.embeddings)
            query_embedding = query_embedding.reshape(1, -1)

            # Calculate similarities
            similarities = cosine_similarity(query_embedding, embeddings_array)[0]

            # Get top matches above threshold
            matches = []
            for i, similarity in enumerate(similarities):
                if similarity >= threshold:
                    chunk = self.chunks[i].copy()
                    chunk["similarity"] = float(similarity)
                    matches.append(chunk)

            # Sort by similarity and return top_k
            matches.sort(key=lambda x: x["similarity"], reverse=True)
            return matches[:top_k]

        except Exception as e:
            print(f"Error searching embeddings: {e}")
            return []

    def get_embedding_stats(self) -> Dict[str, Any]:
        """Get statistics about stored embeddings"""
        try:
            # Calculate file sizes
            total_size = 0
            for file_path in [self.embeddings_file, self.chunks_file, self.metadata_file]:
                if file_path.exists():
                    total_size += file_path.stat().st_size

            return {
                "total_embeddings": len(self.embeddings),
                "total_chunks": len(self.chunks),
                "total_files": len(self.metadata),
                "storage_size_mb": round(total_size / (1024 * 1024), 2),
                "storage_path": str(self.storage_path),
                "files": list(self.metadata.keys()),
                "storage_mode": "local",
            }
        except Exception as e:
            print(f"Error getting stats: {e}")
            return {}

    def clear_embeddings(self, file_path: Optional[str] = None) -> bool:
        """Clear embeddings (all or for specific file)"""
        try:
            if file_path:
                # Clear specific file
                return self._remove_file_embeddings(file_path)
            else:
                # Clear all
                self.embeddings = []
                self.chunks = []
                self.metadata = {}
                return self._save_data()
        except Exception as e:
            print(f"Error clearing embeddings: {e}")
            return False

    def embedding_exists(self, file_path: str) -> bool:
        """Check if embeddings exist for a file"""
        return file_path in self.metadata

    def _remove_file_embeddings(self, file_path: str) -> bool:
        """Remove embeddings for a specific file"""
        if file_path not in self.metadata:
            return True

        try:
            file_meta = self.metadata[file_path]
            start_idx = file_meta["start_idx"]
            end_idx = file_meta["end_idx"]

            # Remove embeddings
            del self.embeddings[start_idx:end_idx + 1]

            # Remove chunks
            self.chunks = [chunk for chunk in self.chunks if chunk.get("file_path") != file_path]

            # Update metadata
            del self.metadata[file_path]

            # Update indices for remaining files
            self._update_indices_after_removal(start_idx, end_idx - start_idx + 1)

            return self._save_data()

        except Exception as e:
            print(f"Error removing file embeddings: {e}")
            return False

    def _update_indices_after_removal(self, removed_start: int, removed_count: int):
        """Update embedding indices after removal"""
        for file_path, meta in self.metadata.items():
            if meta["start_idx"] > removed_start:
                meta["start_idx"] -= removed_count
                meta["end_idx"] -= removed_count

        for chunk in self.chunks:
            if chunk.get("embedding_idx", 0) > removed_start:
                chunk["embedding_idx"] -= removed_count
