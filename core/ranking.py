import datetime


def _hours_old(discovered_at):
    if not discovered_at:
        return 10_000
    if isinstance(discovered_at, datetime.datetime):
        stamp = discovered_at
    else:
        try:
            stamp = datetime.datetime.fromisoformat(str(discovered_at).replace("Z", "+00:00"))
            if stamp.tzinfo is not None:
                stamp = stamp.replace(tzinfo=None)
        except ValueError:
            return 10_000
    return max(0.0, (datetime.datetime.utcnow() - stamp).total_seconds() / 3600)


def freshness_boost(discovered_at):
    """New real webs are boosted so they can surface immediately."""
    hours = _hours_old(discovered_at)
    if hours < 1:
        return 1.0
    if hours < 24:
        return 0.85
    if hours < 72:
        return 0.45
    if hours < 24 * 30:
        return 0.2
    return 0.05


def trust_index(payload):
    """
    Trust is content quality plus structural signals, not raw link count.
    Quality comes from the anti-slop classifier stored at index time.
    """
    quality = float(payload.get("quality_score") or 0.0)
    trust = 0.35 + (quality * 0.45)
    title = (payload.get("title") or "").strip()
    snippet = payload.get("snippet") or ""
    if len(title) > 12 and title.lower() not in {"home", "untitled", "index"}:
        trust += 0.1
    if len(snippet) > 180:
        trust += 0.1
    return min(1.0, trust)


def rootex_smart_rank(semantic_score, payload):
    """
    ROOTEX Smart Ranking (RSR)
    Score = semantic * 0.50 + trust * 0.30 + freshness * 0.20
    """
    semantic = max(0.0, min(1.0, float(semantic_score or 0.0)))
    trust = trust_index(payload)
    fresh = freshness_boost(payload.get("discovered_at"))
    score = (semantic * 0.50) + (trust * 0.30) + (fresh * 0.20)
    return {
        "rsr_score": round(score, 4),
        "semantic": round(semantic, 4),
        "trust": round(trust, 4),
        "freshness": round(fresh, 4),
    }
