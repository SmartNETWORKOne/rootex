import math
import re
from collections import Counter


class RootexQualityScorer:
    """Score real pages from 0 to 1 and reject thin, parked, or repetitive text."""

    def __init__(self):
        self.filler = (
            r"in the ever-evolving landscape",
            r"it'?s important to note",
            r"delve into",
            r"comprehensive guide",
            r"a testament to",
            r"unlock your potential",
            r"in today'?s digital age",
            r"look no further",
        )

    def score_content(self, html_content, clean_text):
        words = re.findall(r"[a-z0-9']+", (clean_text or "").lower())
        count = len(words)
        if count < 40:
            return 0.0

        unique_ratio = len(set(words)) / count
        counts = Counter(words)
        entropy = -sum((n / count) * math.log2(n / count) for n in counts.values())
        density = len(clean_text) / max(len(html_content or ""), 1)
        filler_hits = sum(1 for pattern in self.filler if re.search(pattern, clean_text.lower()))

        score = 0.15
        score += min(0.3, unique_ratio)
        if entropy >= 4.2:
            score += 0.25
        elif entropy >= 3.2:
            score += 0.1
        if 80 <= count <= 2500:
            score += 0.2
        elif count > 2500:
            score += 0.1
        if 0.02 <= density <= 0.65:
            score += 0.15
        score -= filler_hits * 0.12
        if unique_ratio < 0.18:
            score -= 0.35

        return round(max(0.0, min(1.0, score)), 4)
