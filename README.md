# ROOTEX

Search platform by **SmartNETWORK One**.

ROOTEX discovers newly registered domains, waits until they serve real content, then indexes and ranks them immediately. Parked pages, empty hosts, and thin pages stay out of results.

## Pipeline

1. **Discovery** reads Certificate Transparency and stores every new hostname.
2. **Validator** probes each hostname every 10 minutes. DNS failures, parking pages, and empty responses stay in `PROBING`.
3. **Quality filter** scores real pages and rejects thin or repetitive content.
4. **Indexer** embeds accepted pages into Qdrant as soon as they pass.
5. **Ranking** orders results with ROOTEX Smart Ranking:

```
score = semantic * 0.50 + trust * 0.30 + freshness * 0.20
```

Fresh, high-quality pages can outrank older keyword matches.

## Run locally

```bash
docker compose up --build
python3 -m pip install -r requirements.txt
python3 main.py
cd frontend && npm install && npm run dev
```

Open `http://localhost:3000`.

## Vercel

Import this repository in Vercel and set:

- `QDRANT_URL`
- `QDRANT_API_KEY`

Vercel serves the search API. The discovery, validator, and indexer workers must run continuously on a VPS or with Docker, because Vercel functions do not stay awake for the 10-minute probe loop.

## Environment

See `.env.example`.

© 2026 SmartNETWORK One. ROOTEX is a brand of SmartNETWORK One.
