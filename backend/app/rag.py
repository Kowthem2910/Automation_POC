"""
Local RAG retrieval over KB fixtures.

REAL FLOW NOTE:
This POC uses TF-IDF + cosine similarity over a handful of local Markdown
files -- enough to demonstrate the retrieval pattern (chunk, embed, search,
threshold, ground-or-fallback) without needing an embedding model download
or a vector DB server.

In production this module is replaced by:
  - a proper embedding model (e.g. via the Claude/Anthropic embeddings
    endpoint or a dedicated embedding model)
  - a real vector store (OpenSearch / pgvector) instead of an in-memory
    matrix
  - a scheduled/webhook-driven ingestion pipeline that keeps articles in
    sync with Helix, instead of static files loaded once at startup

The public function `search_kb()` is written so that swap can happen
without changing any caller.
"""

from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

KB_DIR = Path(__file__).parent / "kb_data"
MATCH_THRESHOLD = 0.12  # below this, we tell the user we found nothing


class _KBIndex:
    def __init__(self):
        self.articles = []
        self._load()
        self.vectorizer = TfidfVectorizer(stop_words="english")
        texts = [a["title"] + " " + a["body"] for a in self.articles]
        self.matrix = self.vectorizer.fit_transform(texts) if texts else None

    def _load(self):
        for path in sorted(KB_DIR.glob("*.md")):
            raw = path.read_text()
            # naive frontmatter parse
            parts = raw.split("---")
            meta_block = parts[1] if len(parts) > 2 else ""
            body = parts[2].strip() if len(parts) > 2 else raw
            meta = {}
            for line in meta_block.strip().splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip()] = v.strip()
            self.articles.append(
                {
                    "id": meta.get("id", path.stem),
                    "title": meta.get("title", path.stem),
                    "category": meta.get("category", ""),
                    "last_reviewed": meta.get("last_reviewed", ""),
                    "body": body,
                }
            )

    def search(self, query: str, top_k: int = 1):
        if self.matrix is None:
            return []
        qvec = self.vectorizer.transform([query])
        sims = cosine_similarity(qvec, self.matrix)[0]
        ranked = sorted(zip(self.articles, sims), key=lambda x: x[1], reverse=True)
        results = [
            {**article, "score": float(score)}
            for article, score in ranked[:top_k]
            if score >= MATCH_THRESHOLD
        ]
        return results


_index = _KBIndex()


def search_kb(query: str, top_k: int = 1):
    """Public entry point -- production swap target for real embeddings/vector DB."""
    return _index.search(query, top_k=top_k)
