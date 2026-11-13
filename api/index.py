import datetime
import os

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from sentence_transformers import SentenceTransformer

from core.config import COLLECTION_NAME, MODEL_NAME, qdrant_client
from core.ranking import rootex_smart_rank
from models.summarizer import generate_answer

app = FastAPI(title="ROOTEX", version="0.3.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

model = None
qdrant = None


def engine():
    global model, qdrant
    if model is None:
        model = SentenceTransformer(MODEL_NAME)
    if qdrant is None and (os.getenv("QDRANT_URL") or os.getenv("QDRANT_HOST")):
        qdrant = qdrant_client()
    return model, qdrant


@app.get("/api/search")
@app.get("/search")
async def search(q: str = Query(..., min_length=1), limit: int = 10):
    encoder, store = engine()
    if store is None:
        return {
            "query": q,
            "results": [],
            "answer": None,
            "error": "Qdrant is not configured. Set QDRANT_URL or QDRANT_HOST.",
            "brand": "SmartNETWORK One",
            "engine": "ROOTEX",
        }

    hits = store.search(
        collection_name=COLLECTION_NAME,
        query_vector=encoder.encode(q).tolist(),
        limit=max(limit * 3, 15),
    )

    ranked = []
    for hit in hits:
        payload = hit.payload or {}
        scores = rootex_smart_rank(hit.score, payload)
        ranked.append(
            {
                "hostname": payload.get("hostname"),
                "url": payload.get("url") or f"https://{payload.get('hostname')}",
                "title": payload.get("title") or payload.get("hostname"),
                "snippet": payload.get("snippet") or "",
                "quality": payload.get("quality_score", 0),
                **scores,
            }
        )
    ranked.sort(key=lambda item: item["rsr_score"], reverse=True)
    ranked = ranked[:limit]

    answer = generate_answer([item["snippet"] for item in ranked[:3]])

    return {
        "query": q,
        "answer": answer,
        "results": ranked,
        "brand": "SmartNETWORK One",
        "engine": "ROOTEX",
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
    }


@app.get("/api/health")
@app.get("/health")
def health():
    return {"status": "online", "brand": "SmartNETWORK One", "engine": "ROOTEX"}
