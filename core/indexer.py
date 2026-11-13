import asyncio
import logging

import httpx
from bs4 import BeautifulSoup
from qdrant_client.http.models import Distance, PointStruct, VectorParams
from sentence_transformers import SentenceTransformer

from core.config import (
    COLLECTION_NAME,
    MODEL_NAME,
    QUALITY_THRESHOLD,
    USER_AGENT,
    VECTOR_SIZE,
    qdrant_client,
)
from core.database import Domain, get_session
from models.quality import RootexQualityScorer

logging.basicConfig(level=logging.INFO, format="%(asctime)s - ROOTEX/Indexer - %(message)s")


class RootexIndexer:
    def __init__(self):
        self.model = SentenceTransformer(MODEL_NAME)
        self.quality = RootexQualityScorer()
        self.qdrant = qdrant_client()
        self._ensure_collection()

    def _ensure_collection(self):
        names = {item.name for item in self.qdrant.get_collections().collections}
        if COLLECTION_NAME not in names:
            self.qdrant.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
            )

    def clean_html(self, html):
        soup = BeautifulSoup(html, "html.parser")
        for node in soup(["script", "style", "noscript", "header", "footer", "nav", "aside"]):
            node.decompose()
        text = soup.get_text(separator=" ")
        parts = [part.strip() for part in text.splitlines()]
        return " ".join(part for part in parts if part)[:8000]

    async def index_domain(self, domain_obj, client):
        url = f"https://{domain_obj.hostname}"
        try:
            response = await client.get(url, timeout=15.0, follow_redirects=True)
        except Exception:
            response = await client.get(
                f"http://{domain_obj.hostname}", timeout=15.0, follow_redirects=True
            )
        if response.status_code != 200:
            return False

        html = response.text or ""
        clean = self.clean_html(html)
        quality = self.quality.score_content(html, clean)
        if quality < QUALITY_THRESHOLD or len(clean.split()) < 40:
            logging.info("Rejected %.2f %s", quality, domain_obj.hostname)
            return False

        vector = self.model.encode(clean[:2000]).tolist()
        self.qdrant.upsert(
            collection_name=COLLECTION_NAME,
            points=[
                PointStruct(
                    id=domain_obj.id,
                    vector=vector,
                    payload={
                        "hostname": domain_obj.hostname,
                        "title": domain_obj.content_title or domain_obj.hostname,
                        "snippet": clean[:320],
                        "discovered_at": domain_obj.discovered_at.isoformat()
                        if domain_obj.discovered_at
                        else None,
                        "quality_score": quality,
                        "url": str(response.url),
                    },
                )
            ],
        )
        return True

    async def run(self):
        logging.info("ROOTEX Indexer started.")
        headers = {"User-Agent": USER_AGENT}
        async with httpx.AsyncClient(verify=False, headers=headers) as client:
            while True:
                session = get_session()
                try:
                    pending = (
                        session.query(Domain)
                        .filter(Domain.status == "LIVE", Domain.is_indexed == False)
                        .limit(25)
                        .all()
                    )
                    if not pending:
                        await asyncio.sleep(5)
                        continue
                    for domain in pending:
                        try:
                            ok = await self.index_domain(domain, client)
                        except Exception as exc:
                            logging.error("Index failed for %s: %s", domain.hostname, exc)
                            ok = False
                        if ok:
                            domain.is_indexed = True
                            logging.info("Indexed instantly: %s", domain.hostname)
                        else:
                            domain.status = "PROBING"
                    session.commit()
                except Exception as exc:
                    session.rollback()
                    logging.error("Indexer batch failed: %s", exc)
                finally:
                    session.close()
                await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(RootexIndexer().run())
