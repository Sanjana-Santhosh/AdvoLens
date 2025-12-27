import faiss
import numpy as np
import pickle
import os

INDEX_FILE = "faiss_index.bin"
METADATA_FILE = "faiss_metadata.pkl"
VECTOR_DIM = 512  # CLIP output dimension


class FaissManager:
    def __init__(self):
        # IndexFlatIP (Inner Product) works as cosine similarity since vectors are normalized
        self.index = faiss.IndexFlatIP(VECTOR_DIM)
        self.metadata: dict[int, int] = {}  # Map internal ID -> Issue ID
        self.load_index()

    def add_vector(self, embedding: np.ndarray | None, issue_id: int):
        """Adds a vector to the index and maps it to an issue ID."""
        if embedding is None:
            return
        vector = np.array([embedding], dtype=np.float32)
        self.index.add(vector)
        internal_id = self.index.ntotal - 1
        self.metadata[internal_id] = issue_id
        self.save_index()

    def search_similar(self, embedding: np.ndarray | None, k: int = 5, threshold: float = 0.85):
        """
        Search for top-k similar vectors. Returns list of tuples: (issue_id, score)
        """
        if embedding is None or self.index.ntotal == 0:
            return []
        vector = np.array([embedding], dtype=np.float32)
        D, I = self.index.search(vector, k)
        results = []
        for score, internal_id in zip(D[0], I[0]):
            if internal_id != -1 and score >= threshold:
                real_issue_id = self.metadata.get(internal_id)
                if real_issue_id:
                    results.append((real_issue_id, float(score)))
        return results

    def save_index(self):
        faiss.write_index(self.index, INDEX_FILE)
        with open(METADATA_FILE, "wb") as f:
            pickle.dump(self.metadata, f)

    def load_index(self):
        if os.path.exists(INDEX_FILE) and os.path.exists(METADATA_FILE):
            self.index = faiss.read_index(INDEX_FILE)
            with open(METADATA_FILE, "rb") as f:
                self.metadata = pickle.load(f)


# Singleton instance
faiss_manager = FaissManager()
