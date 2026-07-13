"""Pydantic schemas for API request/response validation."""

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, EmailStr, Field


class LeadCreate(BaseModel):
    """Schema for creating a new lead."""
    name: str = Field(..., min_length=1, max_length=255)
    email: str = Field(..., max_length=255)
    job_title: Optional[str] = Field(None, max_length=255)
    company_name: Optional[str] = Field(None, max_length=255)
    company_website: Optional[str] = Field(None, max_length=500)
    company_size: Optional[str] = Field(None, max_length=50)
    industry: Optional[str] = Field(None, max_length=255)
    message: Optional[str] = Field(None)


class LeadResponse(BaseModel):
    """Schema for lead list response."""
    id: str
    created_at: datetime
    name: str
    email: str
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    company_website: Optional[str] = None
    company_size: Optional[str] = None
    industry: Optional[str] = None
    message: Optional[str] = None
    score: Optional[float] = None
    score_reason: Optional[str] = None
    classification: Optional[str] = None
    classification_reason: Optional[str] = None
    status: str
    approval_status: str
    draft_email_subject: Optional[str] = None
    draft_email_body: Optional[str] = None
    routing_action: Optional[str] = None
    routing_reason: Optional[str] = None

    class Config:
        from_attributes = True


class LeadDetailResponse(LeadResponse):
    """Schema for detailed lead response."""
    enriched_industry: Optional[str] = None
    enriched_company_size: Optional[str] = None
    estimated_revenue: Optional[str] = None
    enriched_website: Optional[str] = None
    buying_signals: Any = None
    decision_maker_status: Optional[bool] = None
    market_segment: Optional[str] = None
    industry_score: Optional[float] = None
    company_size_score: Optional[float] = None
    role_score: Optional[float] = None
    buying_intent_score: Optional[float] = None
    error_message: Optional[str] = None
    sent_email_subject: Optional[str] = None
    sent_email_body: Optional[str] = None
    sent_at: Optional[datetime] = None
    edited_email_subject: Optional[str] = None
    edited_email_body: Optional[str] = None
    approval_comment: Optional[str] = None
    injection_attempt_detected: Optional[bool] = False


class ProcessResponse(BaseModel):
    """Schema for lead processing response."""
    lead_id: str
    status: str
    classification: Optional[str] = None
    score: Optional[float] = None
    score_reason: Optional[str] = None
    classification_reason: Optional[str] = None
    routing_action: Optional[str] = None
    draft_email_subject: Optional[str] = None
    draft_email_body: Optional[str] = None
    email_status: Optional[str] = None
    message: str


class ApprovalRequest(BaseModel):
    """Schema for approval action."""
    action: str = Field(..., pattern="^(approve|reject|edit)$")
    comment: Optional[str] = None
    edited_email_subject: Optional[str] = None
    edited_email_body: Optional[str] = None


class DashboardStats(BaseModel):
    """Schema for dashboard statistics."""
    total_leads: int = 0
    hot_leads: int = 0
    nurture_leads: int = 0
    disqualified_leads: int = 0
    average_score: float = 0.0
    approval_rate: float = 0.0
    email_draft_count: int = 0
    pending_approval_count: int = 0
    approved_count: int = 0
    sent_count: int = 0


class GovernanceStats(BaseModel):
    """Schema for governance dashboard statistics."""
    total_audit_events: int = 0
    approval_requests: int = 0
    approved_emails: int = 0
    rejected_emails: int = 0
    sent_emails: int = 0
    governance_violations: int = 0
    injection_attempts_blocked: int = 0
    fairness_tests_passed: int = 0
    fairness_tests_failed: int = 0
    total_fairness_tests: int = 0
    total_injection_tests: int = 0


class AuditLogResponse(BaseModel):
    """Schema for audit log response."""
    id: str
    lead_id: str
    timestamp: datetime
    event_type: str
    input_data: Any = None
    enrichment_results: Any = None
    score: Optional[float] = None
    classification: Optional[str] = None
    classification_reason: Optional[str] = None
    draft_email: Any = None
    approval_status: Optional[str] = None
    final_sent_email: Any = None
    tool_calls: Any = None
    errors: Optional[str] = None
    details: Any = None
    actor: Optional[str] = "system"

    class Config:
        from_attributes = True


class EvaluationResult(BaseModel):
    """Schema for evaluation test results."""
    test_name: str
    status: str  # PASS or FAIL
    details: str
    score: Optional[float] = None
    classification: Optional[str] = None
    expected: str
    actual: str