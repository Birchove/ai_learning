"""Reciprocal Rank Fusion — score(item) = Σ 1/(k + rank_in_list_i)。"""

from typing import Dict, List, Sequence


def rrf_scores(rankings: Sequence[Sequence[str]], k: int = 60) -> Dict[str, float]:
    out: Dict[str, float] = {}
    for ranking in rankings:
        for rank, item in enumerate(ranking, start=1):
            out[item] = out.get(item, 0.0) + 1.0 / (k + rank)
    return out


def rrf_fuse(rankings: Sequence[Sequence[str]], k: int = 60) -> List[str]:
    scores = rrf_scores(rankings, k=k)
    return sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
