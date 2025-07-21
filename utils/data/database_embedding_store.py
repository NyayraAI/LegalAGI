"""
Database-based embedding storage for production/MVP version
"""
import json
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime
from supabase import create_client, Client

from .embedding_store import EmbeddingStore

class DatabaseEmbeddingStore(EmbeddingStore):
    """Database-based embedding storage using Supabase"""
    def __init__(self, config: Dict[str, Any]):
        self.supabase_url = config.get("url", "")
        self.supabase_key = config.get("key", "")

        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Supabase URL and key are required for database storage")

        # Initialize Supabase client
        self.client: Client = create_client(self.supabase_url, self.supabase_key)

        # Table names
        self.embeddings_table = "embeddings"
        self.chunks_table = "chunks"
        self.files_table = "files"

        # Initialize tables if needed
        self._initialize_tables()

    def _initialize_tables(self):
        """Initialize database tables if they don't exist"""
        # This is a placeholder - in production, you'd use migrations
        # For now, we assume tables exist or are created manually
        pass

    def store_embeddings(self, 
                        embeddings: List[np.ndarray], 
                        chunks: List[Dict[str, Any]], 
                        metadata: Dict[str, Any]) -> bool:
        """Store embeddings with associated chunks and metadata"""
        try:
            file_path = metadata.get("file_path", "unknown")

            # Remove existing embeddings for this file
            if self.embedding_exists(file_path):
                self.clear_embeddings(file_path)

            # Insert file metadata
            file_data = {
                "file_path": file_path,
                "chunk_count": len(chunks),
                "metadata": metadata,
                "created_at": datetime.now().isoformat()
            }

            file_result = self.client.table(self.files_table).insert(file_data).execute()
            if not file_result.data:
                return False

            file_id = file_result.data[0]["id"]

            # Insert chunks and embeddings
            for i, (embedding, chunk) in enumerate(zip(embeddings, chunks)):
                # Insert chunk
                chunk_data = {
                    "file_id": file_id,
                    "content": chunk.get("content", ""),
                    "metadata": chunk,
                    "created_at": datetime.now().isoformat()
                }

                chunk_result = self.client.table(self.chunks_table).insert(chunk_data).execute()
                if not chunk_result.data:
                    continue

                chunk_id = chunk_result.data[0]["id"]

                # Insert embedding
                embedding_data = {
                    "chunk_id": chunk_id,
                    "file_id": file_id,
                    "embedding": embedding.tolist(),  # Convert numpy array to list
                    "created_at": datetime.now().isoformat()
                }

                self.client.table(self.embeddings_table).insert(embedding_data).execute()

            return True

        except Exception as e:
            print(f"Error storing embeddings to database: {e}")
            return False

    def search_embeddings(self, 
                         query_embedding: np.ndarray, 
                         top_k: int = 5, 
                         threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Search for similar embeddings using database vector search"""
        try:
            # Note: This is a simplified version
            # In production, you'd use pgvector or similar for efficient vector search

            # Get all embeddings (not efficient for large datasets)
            embeddings_result = self.client.table(self.embeddings_table).select(
                "*, chunks(content, metadata), files(file_path)"
            ).execute()

            if not embeddings_result.data:
                return []

            # Calculate similarities (this should be done in the database in production)
            matches = []
            for row in embeddings_result.data:
                try:
                    stored_embedding = np.array(row["embedding"])

                    # Calculate cosine similarity
                    similarity = np.dot(query_embedding, stored_embedding) / (
                        np.linalg.norm(query_embedding) * np.linalg.norm(stored_embedding)
                    )

                    if similarity >= threshold:
                        chunk_data = row["chunks"]
                        chunk_data["similarity"] = float(similarity)
                        chunk_data["file_path"] = row["files"]["file_path"]
                        matches.append(chunk_data)

                except Exception as e:
                    print(f"Error processing embedding: {e}")
                    continue

            # Sort by similarity and return top_k
            matches.sort(key=lambda x: x["similarity"], reverse=True)
            return matches[:top_k]

        except Exception as e:
            print(f"Error searching embeddings in database: {e}")
            return []

    def get_embedding_stats(self) -> Dict[str, Any]:
        """Get statistics about stored embeddings"""
        try:
            # Get counts from database
            files_result = self.client.table(self.files_table).select("count", count="exact").execute()  # type: ignore
            chunks_result = self.client.table(self.chunks_table).select("count", count="exact").execute()  # type: ignore
            embeddings_result = self.client.table(self.embeddings_table).select("count", count="exact").execute()  # type: ignore

            # Get file list
            files_list_result = self.client.table(self.files_table).select("file_path").execute()
            file_paths = [row["file_path"] for row in files_list_result.data] if files_list_result.data else []

            return {
                "total_embeddings": embeddings_result.count or 0,
                "total_chunks": chunks_result.count or 0,
                "total_files": files_result.count or 0,
                "storage_type": "database",
                "database_url": self.supabase_url,
                "files": file_paths,
                "storage_mode": "database",
            }

        except Exception as e:
            print(f"Error getting database stats: {e}")
            return {}

    def clear_embeddings(self, file_path: Optional[str] = None) -> bool:
        """Clear embeddings (all or for specific file)"""
        try:
            if file_path:
                # Clear specific file
                # Get file ID
                file_result = self.client.table(self.files_table).select("id").eq("file_path", file_path).execute()
                if not file_result.data:
                    return True  # File doesn't exist

                file_id = file_result.data[0]["id"]

                # Delete embeddings
                self.client.table(self.embeddings_table).delete().eq("file_id", file_id).execute()

                # Delete chunks
                self.client.table(self.chunks_table).delete().eq("file_id", file_id).execute()

                # Delete file record
                self.client.table(self.files_table).delete().eq("id", file_id).execute()

            else:
                # Clear all data
                self.client.table(self.embeddings_table).delete().neq("id", 0).execute()
                self.client.table(self.chunks_table).delete().neq("id", 0).execute()
                self.client.table(self.files_table).delete().neq("id", 0).execute()

            return True

        except Exception as e:
            print(f"Error clearing embeddings from database: {e}")
            return False

    def embedding_exists(self, file_path: str) -> bool:
        """Check if embeddings exist for a file"""
        try:
            result = self.client.table(self.files_table).select("id").eq("file_path", file_path).execute()
            return bool(result.data)
        except Exception as e:
            print(f"Error checking if embedding exists: {e}")
            return False

    def _vector_search(self, query_embedding: np.ndarray, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Efficient vector search using pgvector (for production)
        This is a placeholder for the actual implementation
        """

        return []
