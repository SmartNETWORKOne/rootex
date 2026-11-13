import asyncio
import datetime
import logging

import httpx
from bs4 import BeautifulSoup
from sqlalchemy import or_

from core.config import CHECK_INTERVAL_MINUTES, MAX_RETRIES_BEFORE_PARKED, USER_AGENT
from core.database import Domain, get_session

logging.basicConfig(level=logging.INFO, format="%(asctime)s - ROOTEX/Validator - %(message)s")

PARKING_KEYWORDS = (
    "domain is for sale",
    "buy this domain",
    "this domain is parked",
    "parked free",
    "courtesy of godaddy",
    "namecheap parking",
    "sedo.com",
    "this page is under construction",
    "coming soon",
    "account suspended",
    "default web site page",
)


def _title(html):
    soup = BeautifulSoup(html, "html.parser")
    if not soup.title or not soup.title.string:
        return ""
    return " ".join(soup.title.string.split())[:180]


async def check_domain(domain_obj, client):
    url = f"https://{domain_obj.hostname}"
    try:
        response = await client.get(url, timeout=10.0, follow_redirects=True)
    except Exception:
        try:
            response = await client.get(
                f"http://{domain_obj.hostname}", timeout=10.0, follow_redirects=True
            )
        except Exception as exc:
            return "PROBING", f"unreachable: {str(exc)[:40]}"

    if response.status_code != 200:
        return "PROBING", f"status {response.status_code}"

    html = response.text or ""
    lowered = html.lower()
    title = _title(html)
    parked = any(keyword in lowered for keyword in PARKING_KEYWORDS)
    if len(html) > 800 and title and not parked:
        return "LIVE", title
    return "PROBING", "parking or empty"


async def validation_loop():
    logging.info("ROOTEX Validator started. Recheck interval: %s minutes.", CHECK_INTERVAL_MINUTES)
    headers = {"User-Agent": USER_AGENT}
    async with httpx.AsyncClient(verify=False, headers=headers) as client:
        while True:
            session = get_session()
            try:
                cutoff = datetime.datetime.utcnow() - datetime.timedelta(minutes=CHECK_INTERVAL_MINUTES)
                pending = (
                    session.query(Domain)
                    .filter(
                        or_(Domain.last_checked < cutoff, Domain.last_checked == None),
                        Domain.status != "LIVE",
                        Domain.status != "PARKED",
                        Domain.status != "DEAD",
                    )
                    .order_by(Domain.last_checked.asc())
                    .limit(100)
                    .all()
                )
                if not pending:
                    await asyncio.sleep(5)
                    continue

                logging.info("Probing %s domains.", len(pending))
                results = await asyncio.gather(*(check_domain(item, client) for item in pending))
                for domain_obj, (status, meta) in zip(pending, results):
                    domain_obj.last_checked = datetime.datetime.utcnow()
                    domain_obj.check_count = (domain_obj.check_count or 0) + 1
                    if status == "LIVE":
                        domain_obj.status = "LIVE"
                        domain_obj.content_title = meta
                        logging.info("LIVE web ready for instant index: %s", domain_obj.hostname)
                    elif domain_obj.check_count >= MAX_RETRIES_BEFORE_PARKED:
                        domain_obj.status = "PARKED"
                    else:
                        domain_obj.status = "PROBING"
                session.commit()
            except Exception as exc:
                session.rollback()
                logging.error("Validator batch failed: %s", exc)
            finally:
                session.close()
            await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(validation_loop())
