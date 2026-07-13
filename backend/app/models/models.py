"""SQLAlchemy ORM models for LeadFlowAI."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Text, Integer, Float, Boolean, DateTime, JSON, Enum as SAEnum
)
from app.database import Base
import enum


def generate_uuid():
    return str(uuid.uuid4())


def utcnow():
    return datetime.now(timezone.utc)


# --- Enums ---

class LeadStatus(str, enum.Enum):
    PENDING = "PENDING"
    ENRICHED = "ENRICHED"
    SCORED = "SCORED"
    CLASSIFIED = "CLASSIFIED"
    ROUTED = "ROUTED"
    DRAFTED = "DRAFTED"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    SENT = "SENT"
    ARCHIVED = "ARCHIVED"
    ERROR = "ERROR"


class Classification(str, enum.Enum):
    HOT = "HOT"
    NURTURE = "NURTURE"
    DISQUALIFY = "DISQUALIFY"


class ApprovalStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EDITED = "EDITED"


# --- ORM Models ---

class Lead(Base):
    __tablename__ = "leads"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    # Ingestion fields
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    job_title = Column(String(255), nullable=True)
    company_name = Column(String(255), nullable=True)
    company_website = Column(String(500), nullable=True)
    company_size = Column(String(50), nullable=True)
    industry = Column(String(255), nullable=True)
    message = Column(Text, nullable=True)

    # Enrichment results
    enriched_industry = Column(String(255), nullable=True)
    enriched_company_size = Column(String(50), nullable=True)
    estimated_revenue = Column(String(100), nullable=True)
    enriched_website = Column(String(500), nullable=True)
    buying_signals = Column(JSON, nullable=True)
    decision_maker_status = Column(Boolean, nullable=True)
    market_segment = Column(String(100), nullable=True)

    # Scoring
    score = Column(Float, nullable=True)
    score_reason = Column(Text, nullable=True)
    industry_score = Column(Float, nullable=True)
    company_size_score = Column(Float, nullable=True)
    role_score = Column(Float, nullable=True)
    buying_intent_score = Column(Float, nullable=True)

    # Classification
    classification = Column(String(20), nullable=True)
    classification_reason = Column(Text, nullable=True)

    # Routing
    routing_action = Column(String(100), nullable=True)
    routing_reason = Column(Text, nullable=True)

    # Email
    draft_email_subject = Column(String(500), nullable=True)
    draft_email_body = Column(Text, nullable=True)
    email_status = Column(String(50), default="NOT_DRAFTED")

    # Approval
    approval_status = Column(String(20), default=ApprovalStatus.PENDING.value)
    approval_action = Column(String(50), nullable=True)
    approval_comment = Column(Text, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    edited_email_body = Column(Text, nullable=True)
    edited_email_subject = Column(String(500), nullable=True)

    # Final sent email
    sent_email_subject = Column(String(500), nullable=True)
    sent_email_body = Column(Text, nullable=True)
    sent_at = Column(DateTime, nullable=True)

    # Status
    status = Column(String(30), default=LeadStatus.PENDING.value)
    error_message = Column(Text, nullable=True)

    # Fairness / injection test flags
    fairness_verified = Column(Boolean, default=False)
    injection_test_passed = Column(Boolean, default=True)
    injection_attempt_detected = Column(Boolean, default=False)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    lead_id = Column(String(36), nullable=False, index=True)
    timestamp = Column(DateTime, default=utcnow, nullable=False)
    event_type = Column(String(100), nullable=False, index=True)
    input_data = Column(JSON, nullable=True)
    enrichment_results = Column(JSON, nullable=True)
    score = Column(Float, nullable=True)
    classification = Column(String(20), nullable=True)
    classification_reason = Column(Text, nullable=True)
    draft_email = Column(JSON, nullable=True)
    approval_status = Column(String(20), nullable=True)
    final_sent_email = Column(JSON, nullable=True)
    tool_calls = Column(JSON, nullable=True)
    errors = Column(Text, nullable=True)
    details = Column(JSON, nullable=True)
    actor = Column(String(100), nullable=True, default="system")


class FairnessTestResult(Base):
    __tablename__ = "fairness_test_results"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    lead_a_id = Column(String(36), nullable=True)
    lead_b_id = Column(String(36), nullable=True)
    lead_a_name = Column(String(255), nullable=True)
    lead_b_name = Column(String(255), nullable=True)
    score_a = Column(Float, nullable=True)
    score_b = Column(Float, nullable=True)
    classification_a = Column(String(20), nullable=True)
    classification_b = Column(String(20), nullable=True)
    scores_match = Column(Boolean, nullable=True)
    classifications_match = Column(Boolean, nullable=True)
    test_passed = Column(Boolean, nullable=True)
    details = Column(JSON, nullable=True)


class InjectionTestResult(Base):
    __tablename__ = "injection_test_results"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    lead_id = Column(String(36), nullable=True)
    injection_attempt = Column(Text, nullable=True)
    score_returned = Column(Float, nullable=True)
    classification_returned = Column(String(20), nullable=True)
    instruction_followed = Column(Boolean, nullable=True)
    test_passed = Column(Boolean, nullable=True)
    details = Column(JSON, nullable=True)