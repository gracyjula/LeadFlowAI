"""Email Send Tool (Tool C) - Sends emails ONLY after human approval.

CRITICAL RULE: This tool must NEVER execute automatically.
It requires explicit human approval before sending any email.
"""

import logging
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from app.models.models import Lead, ApprovalStatus, LeadStatus

logger = logging.getLogger(__name__)


class EmailSendTool:
    """
    Tool C: Email Send Tool
    
    This tool sends emails but ONLY after explicit human approval.
    It enforces the human approval gate - no bypass paths allowed.
    
    Workflow:
    1. Draft created by agent
    2. Human reviews the draft
    3. Human approves, edits, or rejects
    4. Only approved/edited drafts can be sent
    """

    SEND_BLOCKED_MESSAGE = (
        "EMAIL SEND BLOCKED: Human approval required. "
        "This tool cannot execute automatically. "
        "Please review the draft and approve via the approval endpoint."
    )

    @staticmethod
    def validate_approval(lead: Lead) -> tuple[bool, str]:
        """
        Validate that the lead has proper approval to send.
        
        Returns:
            Tuple of (is_approved, message)
        """
        if not lead:
            return False, "Lead not found"

        if lead.classification != "HOT":
            return False, f"Lead classification is '{lead.classification}'. Only HOT leads can receive outreach."

        if lead.approval_status == ApprovalStatus.PENDING.value:
            return False, EmailSendTool.SEND_BLOCKED_MESSAGE

        if lead.approval_status == ApprovalStatus.REJECTED.value:
            return False, f"Email was rejected by human reviewer. Comment: {lead.approval_comment or 'N/A'}"

        if lead.approval_status == ApprovalStatus.APPROVED.value:
            return True, "Approved"

        if lead.approval_status == ApprovalStatus.EDITED.value:
            return True, "Approved with edits"

        return False, f"Unknown approval status: {lead.approval_status}"

    @staticmethod
    def send_email(db: Session, lead_id: str) -> dict:
        """
        Send an email for an approved lead.
        
        This method checks for human approval before sending.
        Will raise an exception if not approved.
        
        Args:
            db: Database session
            lead_id: ID of the lead
            
        Returns:
            Dictionary with send result
        """
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        
        is_approved, message = EmailSendTool.validate_approval(lead)
        
        if not is_approved:
            raise PermissionError(f"Cannot send email: {message}")

        # Determine which version to send (edited or original)
        subject = lead.edited_email_subject or lead.draft_email_subject
        body = lead.edited_email_body or lead.draft_email_body

        if not subject or not body:
            raise ValueError("No email content to send")

        # Simulate sending the email
        # In production, this would integrate with an email service (SendGrid, SES, etc.)
        logger.info(f"EMAIL SENT to {lead.email}: Subject='{subject}'")

        # Record the sent email
        lead.sent_email_subject = subject
        lead.sent_email_body = body
        lead.sent_at = datetime.now(timezone.utc)
        lead.status = LeadStatus.SENT.value
        lead.email_status = "SENT"
        db.commit()
        db.refresh(lead)

        return {
            "success": True,
            "lead_id": lead_id,
            "to": lead.email,
            "subject": subject,
            "sent_at": lead.sent_at.isoformat(),
            "message": "Email sent successfully after human approval",
        }

    @staticmethod
    def process_approval(
        db: Session,
        lead_id: str,
        action: str,
        comment: Optional[str] = None,
        edited_subject: Optional[str] = None,
        edited_body: Optional[str] = None,
    ) -> dict:
        """
        Process human approval action.
        
        Args:
            db: Database session
            lead_id: Lead ID
            action: 'approve', 'reject', or 'edit'
            comment: Optional reviewer comment
            edited_subject: Edited subject line (for 'edit' action)
            edited_body: Edited email body (for 'edit' action)
            
        Returns:
            Dictionary with approval result
        """
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            raise ValueError(f"Lead {lead_id} not found")

        if action == "approve":
            lead.approval_status = ApprovalStatus.APPROVED.value
            lead.approval_action = "APPROVED"
            lead.approval_comment = comment
            lead.approved_at = datetime.now(timezone.utc)
            lead.status = LeadStatus.APPROVED.value
            message = "Email approved. Ready to send."

        elif action == "reject":
            lead.approval_status = ApprovalStatus.REJECTED.value
            lead.approval_action = "REJECTED"
            lead.approval_comment = comment
            lead.status = LeadStatus.REJECTED.value
            message = "Email rejected."

        elif action == "edit":
            lead.approval_status = ApprovalStatus.EDITED.value
            lead.approval_action = "EDITED"
            lead.approval_comment = comment
            lead.edited_email_subject = edited_subject
            lead.edited_email_body = edited_body
            lead.approved_at = datetime.now(timezone.utc)
            lead.status = LeadStatus.APPROVED.value
            message = "Email edited and approved. Ready to send with edits."

        else:
            raise ValueError(f"Invalid action: {action}")

        db.commit()
        db.refresh(lead)
        logger.info(f"Approval processed for lead {lead_id}: {action}")

        return {
            "success": True,
            "lead_id": lead_id,
            "action": action,
            "message": message,
        }


email_tool = EmailSendTool()