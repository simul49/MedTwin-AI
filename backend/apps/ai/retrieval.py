"""Lexical retrieval over the approved knowledge base (PRD §14).

Deliberately dependency-free: a TF-IDF style lexical scorer over
``knowledge_chunks``. When an embedding provider is configured the same
interface can be backed by vectors; the ranking contract stays identical so the
two can be compared during evaluation (PRD §14.4).
"""
import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import Dict, List, Optional

from apps.ai.models import KnowledgeChunk

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "but", "by", "can", "do", "does",
    "for", "from", "how", "i", "if", "in", "is", "it", "me", "my", "of", "on",
    "or", "so", "that", "the", "this", "to", "was", "what", "when", "which",
    "who", "why", "will", "with", "you", "your",
}

TOKEN_RE = re.compile(r"[\w']+", re.UNICODE)
CJK_RE = re.compile(r"[\u4e00-\u9fff]")


@dataclass
class Passage:
    chunk_id: str
    text: str
    score: float
    source_id: str
    source_title: str
    publisher: str
    source_url: str
    title: str
    review_status: str

    def as_citation(self, index: int) -> dict:
        return {
            "ref": index,
            "chunkId": self.chunk_id,
            "title": self.title or self.source_title,
            "sourceTitle": self.source_title,
            "publisher": self.publisher,
            "url": self.source_url,
            "score": round(self.score, 4),
            "excerpt": self.text[:280],
        }


def tokenize(text: str) -> List[str]:
    """Tokenise English words plus CJK unigrams/bigrams."""
    text = (text or "").lower()
    tokens: List[str] = [t for t in TOKEN_RE.findall(text) if len(t) > 1 and t not in STOPWORDS]

    cjk = "".join(CJK_RE.findall(text))
    for i, ch in enumerate(cjk):
        tokens.append(ch)
        if i + 1 < len(cjk):
            tokens.append(cjk[i : i + 2])
    return tokens


def _tf(tokens: List[str]) -> Counter:
    return Counter(tokens)


def score_chunks(query_tokens: List[str], chunks: List[KnowledgeChunk], idf: Dict[str, float]) -> List[Passage]:
    qtf = _tf(query_tokens)
    passages: List[Passage] = []

    for chunk in chunks:
        ctf = _tf(tokenize(chunk.text))
        if not ctf:
            continue
        score = 0.0
        for term, qcount in qtf.items():
            tf = ctf.get(term, 0)
            if not tf:
                continue
            score += (1 + math.log(tf)) * idf.get(term, 1.0) * (1 + math.log(qcount))
        if score <= 0:
            continue
        # Length normalisation keeps long chunks from dominating.
        length = sum(ctf.values())
        score = score / math.sqrt(length)
        passages.append(
            Passage(
                chunk_id=chunk.id,
                text=chunk.text,
                score=score,
                source_id=chunk.source_id,
                source_title=chunk.source.title if chunk.source_id else "",
                publisher=(chunk.source.publisher if chunk.source_id else "") or "",
                source_url=(chunk.source.source_url if chunk.source_id else "") or "",
                title=chunk.title or "",
                review_status=(chunk.source.review_status if chunk.source_id else "") or "",
            )
        )

    passages.sort(key=lambda p: p.score, reverse=True)
    return passages


def retrieve(
    query: str,
    *,
    top_k: int = 5,
    min_score: float = 0.35,
    clinical: bool = False,
) -> List[Passage]:
    """Return the most relevant approved passages for a query.

    Only ``APPROVED`` sources are ever retrievable, and ``RESTRICTED`` chunks
    require a clinical caller (PRD §14.2).
    """
    query_tokens = tokenize(query)
    if not query_tokens:
        return []

    queryset = (
        KnowledgeChunk.objects.select_related("source")
        .filter(source__review_status="APPROVED")
    )
    if not clinical:
        queryset = queryset.exclude(access_classification="RESTRICTED")

    chunks = list(queryset[:400])
    if not chunks:
        return []

    idf: Dict[str, float] = {}
    doc_freq: Counter = Counter()
    for chunk in chunks:
        doc_freq.update(set(tokenize(chunk.text)))
    total = len(chunks)
    for term, df in doc_freq.items():
        idf[term] = math.log(1 + total / (1 + df))

    passages = score_chunks(query_tokens, chunks, idf)
    return [p for p in passages[:top_k] if p.score >= min_score]


def build_twin_context(patient, categories: Optional[List[str]] = None) -> Dict[str, list]:
    """Collect the patient's own authorised context for grounding.

    Only the categories relevant to the current question are read — the
    assistant retrieves the minimum needed (PRD §11.3).
    """
    wanted = set(categories or ["conditions", "medications", "allergies", "lab_results"])
    context: Dict[str, list] = {}

    if "conditions" in wanted:
        context["conditions"] = [
            {"id": r.id, "title": r.title, "recordedAt": r.recorded_at, "status": r.verification_status}
            for r in patient.health_records.filter(category="CONDITION")[:10]
        ]
    if "medications" in wanted:
        context["medications"] = [
            {"id": m.id, "name": m.name, "dose": m.dose, "frequency": m.frequency, "status": m.status}
            for m in patient.medications.filter(status="ACTIVE")[:10]
        ]
    if "allergies" in wanted:
        context["allergies"] = [
            {"id": a.id, "substance": a.substance, "reaction": a.reaction, "severity": a.severity}
            for a in patient.allergies.filter(status="ACTIVE")[:10]
        ]
    if "lab_results" in wanted:
        context["lab_results"] = [
            {
                "id": o.id,
                "label": o.label,
                "value": str(o.value_numeric) if o.value_numeric is not None else o.value_text,
                "unit": o.unit,
                "flag": o.flag,
                "observedAt": o.observed_at,
            }
            for o in patient.observations.order_by("-observed_at")[:10]
        ]
    return context
