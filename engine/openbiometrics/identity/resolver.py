"""Cross-watchlist identity resolution.

Searches across multiple watchlists to find the best matching
identity for a given face embedding.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from openbiometrics.watchlist.store import SearchResult, WatchlistManager


@dataclass
class MatchEntry:
    """A single match from a specific watchlist."""

    identity_id: str
    label: str
    watchlist_name: str
    similarity: float


@dataclass
class ResolvedIdentity:
    """Best-match identity resolved across multiple watchlists.

    Attributes:
        identity_id: ID of the best-matching identity.
        label: Human-readable label.
        watchlist_name: Which watchlist the best match came from.
        similarity: Cosine similarity of the best match.
        all_matches: All matches across queried watchlists, sorted by
            similarity descending.
    """

    identity_id: str
    label: str
    watchlist_name: str
    similarity: float
    all_matches: list[MatchEntry] = field(default_factory=list)


class IdentityResolver:
    """Resolve identities by searching across multiple watchlists.

    Usage:
        manager = WatchlistManager("./watchlists")
        resolver = IdentityResolver(manager)
        result = resolver.resolve(embedding, watchlist_names=["vip", "staff"])
    """

    def __init__(self, watchlist_manager: WatchlistManager):
        self._manager = watchlist_manager

    def resolve(
        self,
        embedding: np.ndarray,
        watchlist_names: list[str] | None = None,
        threshold: float = 0.4,
        top_k: int = 5,
    ) -> ResolvedIdentity | None:
        """Search across watchlists and return the best match.

        Args:
            embedding: L2-normalized query embedding.
            watchlist_names: Watchlists to search. If None, searches all.
            threshold: Minimum cosine similarity for a match.
            top_k: Max results per watchlist.

        Returns:
            ResolvedIdentity with the best match, or None if no match
            exceeds the threshold.
        """
        names = watchlist_names or self._manager.list_watchlists()

        all_matches: list[MatchEntry] = []
        for name in names:
            watchlist = self._manager.get(name)
            results: list[SearchResult] = watchlist.search(
                embedding, top_k=top_k, threshold=threshold
            )
            for r in results:
                all_matches.append(
                    MatchEntry(
                        identity_id=r.identity_id,
                        label=r.label,
                        watchlist_name=name,
                        similarity=r.similarity,
                    )
                )

        if not all_matches:
            return None

        all_matches.sort(key=lambda m: m.similarity, reverse=True)
        best = all_matches[0]

        return ResolvedIdentity(
            identity_id=best.identity_id,
            label=best.label,
            watchlist_name=best.watchlist_name,
            similarity=best.similarity,
            all_matches=all_matches,
        )
