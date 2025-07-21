from loguru import logger

class SyncEmbeddingStore:
    def __init__(self, local_store, db_store=None):
        self.local = local_store
        self.db = db_store
        self.db_enabled = db_store is not None
        self.sync_queue = []  # Track failed syncs
        self.local_store = local_store
        self.db_store = db_store

    def write(self, embedding_id, data):
        local_success = False
        try:
            self.local.write(embedding_id, data)
            local_success = True
        except Exception as e:
            logger.error(f"Local write failed for {embedding_id}: {e}")
            raise

        if self.db is not None:
            try:
                self.db.write(embedding_id, data)
            except Exception as db_err:
                logger.warning(f"DB write failed for {embedding_id}: {db_err}")
                if local_success:
                    self.sync_queue.append(embedding_id)

    def sync_pending(self):
        """Retry failed DB writes"""
        if not self.db_enabled:
            return

        failed_syncs = []
        for embedding_id in self.sync_queue:
            try:
                if self.db is None:
                    logger.warning(f"Cannot sync {embedding_id}: db store is not available")
                    failed_syncs.append(embedding_id)
                    continue
                data = self.local.read(embedding_id)
                self.db.write(embedding_id, data)
                logger.info(f"Successfully synced {embedding_id}")
            except Exception as e:
                logger.warning(f"Sync retry failed for {embedding_id}: {e}")
                failed_syncs.append(embedding_id)

        self.sync_queue = failed_syncs

    def search_embeddings(self, query_embedding, top_k=5, threshold=0.7):
        """
        Search embeddings by delegating to the local or database store.

        Args:
            query_embedding: numpy array or list representing the query vector
            top_k: number of results to return
            threshold: similarity threshold

        Returns:
            List of matching embeddings from the first available store.
        """
        # Try searching in local_store first
        if self.local_store:
            return self.local_store.search_embeddings(query_embedding, top_k, threshold)

        # Fallback to database store
        if self.db_store:
            return self.db_store.search_embeddings(query_embedding, top_k, threshold)

        # If no stores are available, return empty list
        return []
    
    def store_embeddings(self, embeddings, chunks, metadata):
        local_success = self.local_store.store_embeddings(embeddings, chunks, metadata)
        db_success = True

        if self.db_store:
            try:
                db_success = self.db_store.store_embeddings(embeddings, chunks, metadata)
            except Exception as e:
                logger.warning(f"⚠️ DB store_embeddings failed: {e}")
                db_success = False

        return local_success and db_success
    
    def get_embedding_stats(self):
        return self.local_store.get_embedding_stats()

    def clear_embeddings(self, file_path=None):
        local_success = self.local_store.clear_embeddings(file_path)
        db_success = True

        if self.db_store:
            try:
                db_success = self.db_store.clear_embeddings(file_path)
            except Exception as e:
                logger.warning(f"⚠️ DB clear_embeddings failed: {e}")
                db_success = False

        return local_success and db_success
    
    def embedding_exists(self, file_path: str) -> bool:
        return self.local_store.embedding_exists(file_path)


