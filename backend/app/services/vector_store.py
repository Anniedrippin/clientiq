"""ChromaDB-backed vector store holding historical quarterly reports and
past insights, so new analyses can be grounded against prior findings
(e.g. "was this stockout pattern flagged last quarter too?").
"""

import hashlib
import math
import re

import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb import Documents, EmbeddingFunction, Embeddings

from app.core.config import settings
from app.core.logging_config import get_logger, log_event, Timer

logger = get_logger(__name__)

_EMBED_DIM = 256
_TOKEN_RE = re.compile(r"[a-z0-9]+")


class HashingEmbeddingFunction(EmbeddingFunction):
    """Deterministic, dependency-free embedding function.

    ChromaDB's default embedding function downloads an ONNX model from
    Hugging Face on first use, which fails inside firewalled/offline
    enterprise networks (a very real constraint for consulting clients).
    This feature-hashing embedding needs no network access and no extra
    ML runtime, while still giving semantically-similar text nearby
    vectors via shared-token hashing + simple bigram signal.
    """

    def __call__(self, input: Documents) -> Embeddings:
        return [self._embed(text) for text in input]

    def _embed(self, text: str) -> list[float]:
        vec = [0.0] * _EMBED_DIM
        tokens = _TOKEN_RE.findall(text.lower())
        for tok in tokens:
            idx = int(hashlib.md5(tok.encode()).hexdigest(), 16) % _EMBED_DIM
            vec[idx] += 1.0
        for a, b in zip(tokens, tokens[1:]):
            idx = int(hashlib.md5(f"{a}_{b}".encode()).hexdigest(), 16) % _EMBED_DIM
            vec[idx] += 0.5
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]


class VectorStoreService:
    def __init__(self):
        timer = Timer()
        self._client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            settings.CHROMA_COLLECTION,
            embedding_function=HashingEmbeddingFunction(),
        )
        log_event(
            logger,
            "vector_store_initialized",
            collection=settings.CHROMA_COLLECTION,
            persist_dir=settings.CHROMA_PERSIST_DIR,
            duration_ms=timer.ms(),
        )
        self._seed_if_empty()

    def _seed_if_empty(self):
        if self._collection.count() > 0:
            return
        seed_docs = [
            {
                "id": "report-q1-2026-north",
                "text": (
                    "Q1 2026 North region report: revenue grew 4% QoQ. Inventory stockout rate "
                    "was stable at 10-11% across core SKU categories. No material churn events "
                    "linked to fulfillment. Delivery delay tickets averaged 2.1 days."
                ),
                "metadata": {"region": "North", "quarter": "Q1-2026", "type": "quarterly_report"},
            },
            {
                "id": "report-q4-2025-north",
                "text": (
                    "Q4 2025 North region report: revenue grew 7% QoQ driven by seasonal demand. "
                    "Warehouse Equipment SKU stockouts flagged as an emerging risk at 9% rate, "
                    "recommended increasing safety stock ahead of Q1."
                ),
                "metadata": {"region": "North", "quarter": "Q4-2025", "type": "quarterly_report"},
            },
        ]
        self.add_documents(seed_docs)

    def add_documents(self, docs: list[dict]):
        timer = Timer()
        self._collection.upsert(
            ids=[d["id"] for d in docs],
            documents=[d["text"] for d in docs],
            metadatas=[d["metadata"] for d in docs],
        )
        log_event(
            logger,
            "vector_store_documents_upserted",
            count=len(docs),
            duration_ms=timer.ms(),
        )

    def query(self, query_text: str, n_results: int = 3, region: str | None = None) -> list[dict]:
        timer = Timer()
        log_event(logger, "vector_store_query_started", query=query_text, n_results=n_results, region=region)
        where = {"region": region} if region else None
        try:
            results = self._collection.query(query_texts=[query_text], n_results=n_results, where=where)
            docs = []
            ids = results.get("ids", [[]])[0]
            documents = results.get("documents", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]
            distances = results.get("distances", [[]])[0] if results.get("distances") else [None] * len(ids)
            for doc_id, text, meta, dist in zip(ids, documents, metadatas, distances):
                docs.append({"id": doc_id, "text": text, "metadata": meta, "distance": dist})
            log_event(
                logger,
                "vector_store_query_completed",
                status="success",
                result_count=len(docs),
                duration_ms=timer.ms(),
            )
            return docs
        except Exception as exc:  # noqa: BLE001
            log_event(
                logger,
                "vector_store_query_failed",
                level="error",
                status="error",
                error=str(exc),
                duration_ms=timer.ms(),
            )
            return []


vector_store = VectorStoreService()
