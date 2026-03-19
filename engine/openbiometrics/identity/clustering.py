"""Face embedding clustering and deduplication.

Uses cosine similarity with union-find to group embeddings into
identity clusters without requiring HDBSCAN or other external
dependencies beyond numpy.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class DuplicateGroup:
    """A group of duplicate identities found during deduplication.

    Attributes:
        indices: Indices into the original embeddings array.
        labels: Corresponding labels for each index.
        mean_similarity: Average pairwise cosine similarity within the group.
    """

    indices: list[int]
    labels: list[str]
    mean_similarity: float


class _UnionFind:
    """Simple union-find (disjoint set) data structure."""

    def __init__(self, n: int):
        self._parent = list(range(n))
        self._rank = [0] * n

    def find(self, x: int) -> int:
        while self._parent[x] != x:
            self._parent[x] = self._parent[self._parent[x]]
            x = self._parent[x]
        return x

    def union(self, x: int, y: int) -> None:
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            return
        if self._rank[rx] < self._rank[ry]:
            rx, ry = ry, rx
        self._parent[ry] = rx
        if self._rank[rx] == self._rank[ry]:
            self._rank[rx] += 1

    def groups(self) -> dict[int, list[int]]:
        """Return connected components as {root: [members]}."""
        components: dict[int, list[int]] = {}
        for i in range(len(self._parent)):
            root = self.find(i)
            components.setdefault(root, []).append(i)
        return components


class FaceClusterer:
    """Cluster face embeddings by cosine similarity using union-find.

    Usage:
        clusterer = FaceClusterer()
        groups = clusterer.cluster(embeddings, threshold=0.6)
        # groups: [[0, 3, 7], [1, 4], [2], ...]
    """

    def cluster(
        self,
        embeddings: np.ndarray,
        threshold: float = 0.6,
    ) -> list[list[int]]:
        """Cluster embeddings into identity groups.

        Builds a cosine similarity matrix and uses union-find to merge
        pairs exceeding the threshold into connected components.

        Args:
            embeddings: (N, D) array of L2-normalized face embeddings.
            threshold: Minimum cosine similarity to link two embeddings.

        Returns:
            List of index groups, each group representing one identity.
        """
        n = embeddings.shape[0]
        if n == 0:
            return []

        # Cosine similarity matrix (assumes L2-normalized input)
        sim = embeddings @ embeddings.T

        uf = _UnionFind(n)
        for i in range(n):
            for j in range(i + 1, n):
                if sim[i, j] >= threshold:
                    uf.union(i, j)

        return list(uf.groups().values())

    def deduplicate(
        self,
        embeddings: np.ndarray,
        labels: list[str],
        threshold: float = 0.7,
    ) -> list[DuplicateGroup]:
        """Find groups of duplicate identities.

        Args:
            embeddings: (N, D) array of L2-normalized face embeddings.
            labels: Label for each embedding (parallel list).
            threshold: Minimum cosine similarity to consider duplicates.

        Returns:
            List of DuplicateGroup for groups with 2+ members.
        """
        groups = self.cluster(embeddings, threshold=threshold)

        # Pre-compute similarity matrix once
        sim = embeddings @ embeddings.T

        duplicates: list[DuplicateGroup] = []
        for indices in groups:
            if len(indices) < 2:
                continue

            # Mean pairwise similarity within the group
            pair_sims: list[float] = []
            for i_pos, i in enumerate(indices):
                for j in indices[i_pos + 1 :]:
                    pair_sims.append(float(sim[i, j]))

            duplicates.append(
                DuplicateGroup(
                    indices=indices,
                    labels=[labels[i] for i in indices],
                    mean_similarity=float(np.mean(pair_sims)),
                )
            )

        return duplicates
