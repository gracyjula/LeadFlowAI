"""Audit logging service for recording all lead processing events."""

import json
import logging
from datetime import datetime, timezone
from typing import Optional, Any
from sqlalchemy.orm import Session
from app.models.models import AuditLog

logger = logging.getLogger(__name__)


class AuditService:
    """Service for recording comprehensive audit logs."""

    @staticmethod
    def log_event(
        db: Session,
        lead_id: str,
        event_type: str,
        input_data: Optional[dict] = None,
        enrichment_results: Optional[dict] = None,
        score: Optional[float] = None,
        classification: Optional[str] = None,
        classification_reason: Optional[str] = None,
        draft_email: Optional[dict] = None,
        approval_status: Optional[str] = None,
        final_sent_email: Optional[dict] = None,
        tool_calls: Optional[list] = None,
        errors: Optional[str] = None,
        details: Optional[dict] = None,
        actor: Optional[str] = "system",
    ) -> AuditLog:
        """Create a new audit log entry."""
        log_entry = AuditLog(
            lead_id=lead_id,
            event_type=event_type,
            input_data=input_data,
            enrichment_results=enrichment_results,
            score=score,
            classification=classification,
            classification_reason=classification_reason,
            draft_email=draft_email,
            approval_status=approval_status,
            final_sent_email=final_sent_email,
            tool_calls=tool_calls,
            errors=errors,
            details=details,
            actor=actor,
        )
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
        logger.info(f"Audit log created: {event_type} for lead {lead_id}")
        return log_entry

    @staticmethod
    def get_lead_logs(db: Session, lead_id: str) -> list[AuditLog]:
        """Get all audit logs for a specific lead."""
        return (
            db.query(AuditLog)
            .filter(AuditLog.lead_id == lead_id)
            .order_by(AuditLog.timestamp.asc())
            .all()
        )

    @staticmethod
    def get_all_logs(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        event_type: Optional[str] = None,
    ) -> list[AuditLog]:
        """Get all audit logs with optional filtering."""
        query = db.query(AuditLog)
        if event_type:
            query = query.filter(AuditLog.event_type == event_type)
        return query.order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit).all()


audit_service = AuditService()