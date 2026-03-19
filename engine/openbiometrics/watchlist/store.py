"""FAISS-based watchlist for 1:N face identification.

Supports:
- Add/remove identities
- Search by embedding (1:N identification)
- Persist to disk
- Multiple watchlists (collections)
"""

from __future__ import annotations

import json
import threading
from dataclasses import dataclass
from pathlib import Path

import faiss
import numpy as np


@dataclass
class SearchResult:
    """A single search result from the watchlist."""

    identity_id: str
    label: str
    similarity: float
    metadata: dict


class Watchlist:
    """Thread-safe FAISS-backed face watchlist.

    Uses inner product (cosine similarity on L2-normalized vectors)
    for fast approximate nearest neighbor search.
    """

    EMBEDDING_DIM = 512

    def __init__(self, name: str = "default"):
        self.name = name
        self._index = faiss.IndexFlatIP(self.EMBEDDING_DIM)  # Inner product = cosine for normalized
        self._identities: list[dict] = []  # Parallel list: [{id, label, metadata}, ...]
        self._lock = threading.Lock()

    @property
    def size(self) -> int:
        return self._index.ntotal

    def add(
        self,
        identity_id: str,
        label: str,
        embedding: np.ndarray,
        metadata: dict | None = None,
    ) -> None:
        """Add a face embedding to the watchlist.

        Args:
            identity_id: Unique identifier
            label: Human-readable name
            embedding: L2-normalized 512-d embedding
            metadata: Optional extra data
        """
        embedding = embedding.reshape(1, -1).astype(np.float32)
        with self._lock:
            self._index.add(embedding)
            self._identities.append(
                {"id": identity_id, "label": label, "metadata": metadata or {}}
            )

    def search(
        self, embedding: np.ndarray, top_k: int = 5, threshold: float = 0.4
    ) -> list[SearchResult]:
        """Search for matching identities.

        Args:
            embedding: Query embedding (L2-normalized)
            top_k: Maximum results to return
            threshold: Minimum cosine similarity

        Returns:
            List of SearchResult sorted by similarity descending
        """
        if self.size == 0:
            return []

        embedding = embedding.reshape(1, -1).astype(np.float32)
        k = min(top_k, self.size)

        with self._lock:
            similarities, indices = self._index.search(embedding, k)

        results = []
        for sim, idx in zip(similarities[0], indices[0]):
            if idx < 0 or sim < threshold:
                continue
            identity = self._identities[idx]
            results.append(
                SearchResult(
                    identity_id=identity["id"],
                    label=identity["label"],
                    similarity=float(sim),
                    metadata=identity["metadata"],
                )
            )

        return results

    def remove(self, identity_id: str) -> bool:
        """Remove an identity by ID. Rebuilds the index."""
        with self._lock:
            idx = None
            for i, ident in enumerate(self._identities):
                if ident["id"] == identity_id:
                    idx = i
                    break

            if idx is None:
                return False

            # Rebuild index without the removed entry
            all_vectors = faiss.rev_swig_ptr(
                self._index.get_xb(), self.size * self.EMBEDDING_DIM
            ).reshape(-1, self.EMBEDDING_DIM).copy()

            remaining = np.delete(all_vectors, idx, axis=0)
            self._identities.pop(idx)

            self._index.reset()
            if len(remaining) > 0:
                self._index.add(remaining)

            return True

    def save(self, directory: str) -> None:
        """Persist watchlist to disk."""
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)

        faiss.write_index(self._index, str(path / f"{self.name}.faiss"))
        with open(path / f"{self.name}.json", "w") as f:
            json.dump(self._identities, f)

    def load(self, directory: str) -> None:
        """Load watchlist from disk."""
        path = Path(directory)

        index_path = path / f"{self.name}.faiss"
        meta_path = path / f"{self.name}.json"

        if not index_path.exists():
            return

        with self._lock:
            self._index = faiss.read_index(str(index_path))
            with open(meta_path) as f:
                self._identities = json.load(f)


class WatchlistManager:
    """Manages multiple named watchlists."""

    def __init__(self, storage_dir: str = "./watchlists"):
        self.storage_dir = storage_dir
        self._watchlists: dict[str, Watchlist] = {}

    def get(self, name: str = "default") -> Watchlist:
        """Get or create a watchlist by name."""
        if name not in self._watchlists:
            wl = Watchlist(name)
            wl.load(self.storage_dir)
            self._watchlists[name] = wl
        return self._watchlists[name]

    def delete(self, name: str) -> bool:
        """Delete a watchlist."""
        if name in self._watchlists:
            del self._watchlists[name]
        path = Path(self.storage_dir)
        removed = False
        for ext in (".faiss", ".json"):
            f = path / f"{name}{ext}"
            if f.exists():
                f.unlink()
                removed = True
        return removed

    def list_watchlists(self) -> list[str]:
        """List all watchlists (loaded + on disk)."""
        names = set(self._watchlists.keys())
        path = Path(self.storage_dir)
        if path.exists():
            for f in path.glob("*.faiss"):
                names.add(f.stem)
        return sorted(names)

    def save_all(self) -> None:
        """Persist all loaded watchlists."""
        for wl in self._watchlists.values():
            wl.save(self.storage_dir)
