import datetime
import logging

import certstream

from core.database import Domain, get_session

logging.basicConfig(level=logging.INFO, format="%(asctime)s - ROOTEX/Discovery - %(message)s")


def _remember(session, hostname):
    hostname = hostname.strip().lower().rstrip(".")
    if hostname.startswith("*."):
        hostname = hostname[2:]
    if not hostname or " " in hostname or "." not in hostname:
        return
    exists = session.query(Domain).filter_by(hostname=hostname).first()
    if exists:
        return
    session.add(
        Domain(
            hostname=hostname,
            last_checked=datetime.datetime.utcnow() - datetime.timedelta(minutes=11),
            status="DISCOVERED",
        )
    )
    logging.info("New domain discovered: %s", hostname)


def handle_callback(message, context):
    if message.get("message_type") != "certificate_update":
        return

    names = message.get("data", {}).get("leaf_cert", {}).get("all_domains", [])
    session = get_session()
    try:
        for hostname in names:
            _remember(session, hostname)
        session.commit()
    except Exception as exc:
        session.rollback()
        logging.error("Discovery write failed: %s", exc)
    finally:
        session.close()


def start_discovery():
    logging.info("ROOTEX Discovery Engine starting. Listening to Certificate Transparency.")
    certstream.listen_for_events(handle_callback, url="wss://certstream.calidog.io/")


if __name__ == "__main__":
    start_discovery()
