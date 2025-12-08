import os
from typing import List, Tuple
import pandas as pd


class SimpleRetriever:
    """
    Minimal text retriever over KPI catalogue (name + description).
    This is a lightweight placeholder until a vector index (FAISS/Chroma) is added.
    """
    def __init__(self, catalogue: pd.DataFrame):
        self.catalogue = catalogue.copy() if catalogue is not None else pd.DataFrame()

    def search(self, query: str, top_k: int = 5) -> List[Tuple[str, str]]:
        """
        Return top_k KPI entries (id, text) whose name/description contain query tokens.
        """
        if self.catalogue is None or self.catalogue.empty or not query:
            return []

        q = query.lower()
        scored = []
        for _, row in self.catalogue.iterrows():
            text = f"{row.get('kpi_name','')} {row.get('kpi_description','')}".lower()
            score = sum(1 for token in q.split() if token in text)
            scored.append((score, row.get('kpi_id', ''), row.get('kpi_name', ''), row.get('kpi_description', '')))

        scored = sorted(scored, key=lambda x: x[0], reverse=True)
        results = []
        for score, kpi_id, name, desc in scored[:top_k]:
            snippet = f"{name}: {desc}"
            results.append((kpi_id, snippet))
        return results


def build_retriever(catalogue: pd.DataFrame) -> SimpleRetriever:
    return SimpleRetriever(catalogue)
