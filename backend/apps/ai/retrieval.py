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


def _best_window(text: str, query_tokens: set, size: int = 600) -> str:
    """Return the ~``size``-char window of the text with the most query matches."""
    lines = [ln for ln in text.splitlines() if ln.strip()]
    best, best_score = "", -1
    window: List[str] = []
    length = 0
    for line in lines:
        window.append(line)
        length += len(line) + 1
        while length > size and window:
            length -= len(window[0]) + 1
            window.pop(0)
        candidate = " ".join(window)
        score = len(query_tokens & set(tokenize(candidate)))
        # '>=' prefers the largest window on ties, so matched lines keep
        # their following context instead of truncating at the first hit.
        if score >= best_score:
            best_score, best = score, candidate
    return best or text[:size]


def retrieve_patient_documents(patient, query: str, top_k: int = 2, min_score: float = 0.3) -> List[Passage]:
    """Search the patient's own uploaded documents (OCR/text extraction output).

    Personal context: only the caller's own PROCESSED documents are searched,
    and the passage is clearly titled so the UI cites it as a personal document
    rather than medical literature (PRD §11.3 data minimisation).
    """
    from apps.twin.models import Document

    query_tokens = set(tokenize(query))
    if not query_tokens:
        return []

    docs = list(
        patient.documents.filter(processing_status="PROCESSED")
        .exclude(extracted_text__isnull=True)
        .order_by("-created_at")[:30]
    )

    passages: List[Passage] = []
    seen_content: set = set()
    for doc in docs:
        text = (doc.extracted_text or "").strip()
        if not text or len(text) < 60:
            continue
        # Re-uploads of the same file are common — keep the most recent copy.
        content_key = re.sub(r"\s+", "", text[:120].lower())
        if content_key in seen_content:
            continue
        seen_content.add(content_key)
        # Match on both the document name (e.g. a quoted filename in the
        # question) and its extracted content.
        doc_tokens = set(tokenize(doc.name)) | set(tokenize(text))
        overlap = len(query_tokens & doc_tokens)
        score = overlap / len(query_tokens)
        if score < min_score or overlap < 2:
            continue
        passages.append(
            Passage(
                chunk_id=f"doc:{doc.id}",
                text=_best_window(text, query_tokens),
                score=score,
                source_id="",
                source_title="Your uploaded documents",
                publisher="",
                source_url="",
                title=f"Document: {doc.name}",
                review_status="PERSONAL",
            )
        )

    passages.sort(key=lambda p: p.score, reverse=True)

    # Generic phrasing ("summarize my document") carries no content tokens —
    # fall back to the most recent processed document so the question still
    # gets a real answer in real time.
    if not passages:
        intent_words = {"document", "doc", "report", "prescription", "summary",
                        "summarize", "scan", "file", "upload", "uploaded", "record"}
        if query_tokens & intent_words and docs:
            doc = docs[0]
            text = (doc.extracted_text or "").strip()
            if text:
                passages.append(
                    Passage(
                        chunk_id=f"doc:{doc.id}",
                        text=text[:600],
                        score=0.3,
                        source_id="",
                        source_title="Your uploaded documents",
                        publisher="",
                        source_url="",
                        title=f"Document: {doc.name}",
                        review_status="PERSONAL",
                    )
                )

    return passages[:top_k]


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
