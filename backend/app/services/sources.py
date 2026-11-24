import hashlib
import json

from sqlalchemy.orm import Session

from ..models import SourceDocument


def record_source(
    db: Session,
    user_id: int,
    source_type: str,
    title: str,
    url: str,
    payload,
    retrieved_at,
):
    """Save a record of where data came from. Never breaks the request if saving fails."""
    try:
        digest = hashlib.sha256(
            json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()

        existing = (
            db.query(SourceDocument)
            .filter(
                SourceDocument.user_id == user_id,
                SourceDocument.source_type == source_type,
                SourceDocument.title == title,
                SourceDocument.content_hash == digest,
            )
            .first()
        )
        if existing:
            existing.retrieved_at = retrieved_at
        else:
            db.add(
                SourceDocument(
                    user_id=user_id,
                    source_type=source_type,
                    title=title,
                    source_url=url,
                    retrieved_at=retrieved_at,
                    content_hash=digest,
                )
            )
        db.commit()
    except Exception:
        db.rollback()