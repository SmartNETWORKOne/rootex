"""
Lightweight extractive answer for zero-click results.

A full transformer summarizer is too heavy for the Vercel function, so ROOTEX
builds a short answer from the highest-ranked real snippets.
"""


def generate_answer(snippets, limit=280):
    parts = []
    for snippet in snippets:
        text = " ".join((snippet or "").split())
        if text and text not in parts:
            parts.append(text)
        if sum(len(part) for part in parts) >= limit:
            break
    if not parts:
        return None
    answer = " ".join(parts)
    if len(answer) > limit:
        answer = answer[: limit - 1].rsplit(" ", 1)[0] + "…"
    return answer
