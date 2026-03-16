import faiss
import numpy as np
import pickle
import os
from app.core.ml_debug_log import add_ml_debug_log

INDEX_FILE = "faiss_index.bin"
METADATA_FILE = "faiss_metadata.pkl"
VECTOR_DIM = 512  # CLIP output dimension


class FaissManager:
    def __init__(self):
        # IndexFlatIP (Inner Product) works as cosine similarity since vectors are normalized
        self.index = faiss.IndexFlatIP(VECTOR_DIM)
        self.metadata: dict[int, int] = {}  # Map internal ID -> Issue ID
        add_ml_debug_log(
            component="faiss",
            operation="init",
            message="Faiss manager initialized",
            details={"vector_dim": VECTOR_DIM},
        )
        self.load_index()

    def add_vector(self, embedding: np.ndarray | None, issue_id: int, persist: bool = True):
        """Adds a vector to the index and maps it to an issue ID."""
        if embedding is None:
            add_ml_debug_log(
                component="faiss",
                operation="add_vector",
                level="WARNING",
                message="Skipped add because embedding is None",
                details={"issue_id": issue_id, "persist": persist},
            )
            return
        vector = np.array([embedding], dtype=np.float32)
        self.index.add(vector)
        internal_id = self.index.ntotal - 1
        self.metadata[internal_id] = issue_id
        add_ml_debug_log(
            component="faiss",
            operation="add_vector",
            message="Vector added to Faiss index",
            details={
                "issue_id": issue_id,
                "internal_id": int(internal_id),
                "index_size": int(self.index.ntotal),
                "persist": persist,
            },
        )
        if persist:
            self.save_index()

    def reset_index(self, persist: bool = True):
        """Resets the in-memory index and metadata mapping."""
        old_size = int(self.index.ntotal)
        self.index = faiss.IndexFlatIP(VECTOR_DIM)
        self.metadata = {}
        add_ml_debug_log(
            component="faiss",
            operation="reset_index",
            message="Faiss index reset",
            details={"old_size": old_size, "new_size": 0, "persist": persist},
        )
        if persist:
            self.save_index()

    def search_similar(self, embedding: np.ndarray | None, k: int = 5, threshold: float = 0.85):
        """
        Search for top-k similar vectors. Returns list of tuples: (issue_id, score)
        """
        if embedding is None:
            add_ml_debug_log(
                component="faiss",
                operation="search_similar",
                level="WARNING",
                message="Search skipped because embedding is None",
                details={"k": k, "threshold": threshold},
            )
            return []

        if self.index.ntotal == 0:
            add_ml_debug_log(
                component="faiss",
                operation="search_similar",
                level="DEBUG",
                message="Search skipped because Faiss index is empty",
                details={"k": k, "threshold": threshold},
            )
            return []

        vector = np.array([embedding], dtype=np.float32)
        D, I = self.index.search(vector, k)
        results = []
        for score, internal_id in zip(D[0], I[0]):
            if internal_id != -1 and score >= threshold:
                real_issue_id = self.metadata.get(internal_id)
                if real_issue_id:
                    results.append((real_issue_id, float(score)))

        add_ml_debug_log(
            component="faiss",
            operation="search_similar",
            message="Faiss similarity search completed",
            details={
                "k": k,
                "threshold": threshold,
                "index_size": int(self.index.ntotal),
                "results_count": len(results),
                "top_score": float(results[0][1]) if results else None,
            },
        )
        return results

    def save_index(self):
        faiss.write_index(self.index, INDEX_FILE)
        with open(METADATA_FILE, "wb") as f:
            pickle.dump(self.metadata, f)
        add_ml_debug_log(
            component="faiss",
            operation="save_index",
            message="Faiss index persisted to disk",
            details={"index_size": int(self.index.ntotal), "metadata_size": len(self.metadata)},
        )

    def load_index(self):
        if os.path.exists(INDEX_FILE) and os.path.exists(METADATA_FILE):
            self.index = faiss.read_index(INDEX_FILE)
            with open(METADATA_FILE, "rb") as f:
                self.metadata = pickle.load(f)
            add_ml_debug_log(
                component="faiss",
                operation="load_index",
                message="Faiss index loaded from disk",
                details={"index_size": int(self.index.ntotal), "metadata_size": len(self.metadata)},
            )
        else:
            add_ml_debug_log(
                component="faiss",
                operation="load_index",
                level="DEBUG",
                message="No persisted Faiss index found; using empty in-memory index",
                details={"index_file": INDEX_FILE, "metadata_file": METADATA_FILE},
            )


# Singleton instance
faiss_manager = FaissManager()
