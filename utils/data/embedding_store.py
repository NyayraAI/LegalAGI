"""
Abstract base class and factory for embedding storage
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from datetime import datetime

class EmbeddingStore(ABC):
    """Abstract base class for embedding storage"""
    
    @abstractmethod
    def store_embeddings(self, 
                        embeddings: List[np.ndarray], 
                        chunks: List[Dict[str, Any]], 
                        metadata: Dict[str, Any]) -> bool:
        """
        Store embeddings with associated chunks and metadata
        
        Args:
            embeddings: List of embedding vectors
            chunks: List of text chunks with metadata
            metadata: Additional metadata (file info, etc.)
            
        Returns:
            bool: True if successful
        """
        pass
    
    @abstractmethod
    def search_embeddings(self, 
                         query_embedding: np.ndarray, 
                         top_k: int = 5, 
                         threshold: float = 0.7) -> List[Dict[str, Any]]:
        """
        Search for similar embeddings
        
        Args:
            query_embedding: Query vector
            top_k: Number of results to return
            threshold: Similarity threshold
            
        Returns:
            List of matching chunks with similarity scores
        """
        pass
    
    @abstractmethod
    def get_embedding_stats(self) -> Dict[str, Any]:
        """
        Get statistics about stored embeddings
        
        Returns:
            Dictionary with stats (count, storage size, etc.)
        """
        pass
    
    @abstractmethod
    def clear_embeddings(self, file_path: Optional[str] = None) -> bool:
        """
        Clear embeddings (all or for specific file)
        
        Args:
            file_path: If provided, only clear embeddings for this file
            
        Returns:
            bool: True if successful
        """
        pass
    
    @abstractmethod
    def embedding_exists(self, file_path: str) -> bool:
        """
        Check if embeddings exist for a file
        
        Args:
            file_path: Path to check
            
        Returns:
            bool: True if embeddings exist
        """
        pass

class EmbeddingStoreFactory:
    """Factory class to create appropriate embedding store"""
    
    @staticmethod
    def create_store(storage_config: Dict[str, Any]) -> EmbeddingStore:
        """
        Create embedding store based on configuration
        
        Args:
            storage_config: Storage configuration dict
            
        Returns:
            EmbeddingStore instance
        """
        storage_type = storage_config.get("type", "local")
        
        if storage_type == "local":
            from .local_embedding_store import LocalEmbeddingStore
            return LocalEmbeddingStore(storage_config)
        elif storage_type == "database":
            from .database_embedding_store import DatabaseEmbeddingStore
            return DatabaseEmbeddingStore(storage_config)
        else:
            raise ValueError(f"Unknown storage type: {storage_type}")