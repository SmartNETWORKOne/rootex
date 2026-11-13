import os

MODEL_NAME = os.getenv("ROOTEX_MODEL", "all-MiniLM-L6-v2")
COLLECTION_NAME = os.getenv("ROOTEX_COLLECTION", "rootex_web_index")
VECTOR_SIZE = 384

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))

CHECK_INTERVAL_MINUTES = int(os.getenv("ROOTEX_CHECK_INTERVAL_MINUTES", "10"))
MAX_RETRIES_BEFORE_PARKED = int(os.getenv("ROOTEX_MAX_RETRIES", "144"))
QUALITY_THRESHOLD = float(os.getenv("ROOTEX_QUALITY_THRESHOLD", "0.4"))

USER_AGENT = os.getenv(
    "ROOTEX_USER_AGENT",
    "ROOTEXBot/0.3 (+https://rootex.smartnetwork.one; SmartNETWORK One)",
)


def qdrant_client():
    """Connect to Qdrant Cloud when QDRANT_URL is set, otherwise the local node."""
    from qdrant_client import QdrantClient

    if QDRANT_URL:
        return QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    return QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
