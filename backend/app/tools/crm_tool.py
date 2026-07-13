"""CRM Write Tool (Tool B) - Writes lead data to the CRM database."""

import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.models import Lead, LeadStatus

logger = logging.getLogger(__name__)


class CRMWriteTool:
    """
    Tool B: CRM Write Tool
    
    Responsible for writing lead data to the CRM database.
    Allowed operations: create, update, archive leads.
    """

    @staticmethod
    def create_lead(db: Session, lead_data: dict) -> Lead:
        """Create a new lead in the CRM."""
        lead = Lead(
            name=lead_data.get("name"),
            email=lead_data.get("email"),
            job_title=lead_data.get("job_title"),
            company_name=lead_data.get("company_name"),
            company_website=lead_data.get("company_website"),
            company_size=lead_data.get("company_size"),
            industry=lead_data.get("industry"),
            message=lead_data.get("message"),
            status=LeadStatus.PENDING.value,
        )
        db.add(lead)
        db.commit()
        db.refresh(lead)
        logger.info(f"Lead created in CRM: {lead.id}")
        return lead

    @staticmethod
    def update_lead(db: Session, lead_id: str, update_data: dict) -> Lead:
        """Update an existing lead in the CRM."""
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            raise ValueError(f"Lead {lead_id} not found")

        for key, value in update_data.items():
            if hasattr(lead, key) and value is not None:
                setattr(lead, key, value)

        lead.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(lead)
        logger.info(f"Lead updated in CRM: {lead_id}")
        return lead

    @staticmethod
    def archive_lead(db: Session, lead_id: str, reason: str = None) -> Lead:
        """Archive a lead in the CRM."""
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            raise ValueError(f"Lead {lead_id} not found")

        lead.status = LeadStatus.ARCHIVED.value
        lead.routing_action = "ARCHIVED"
        lead.routing_reason = reason or "Lead disqualified"
        lead.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(lead)
        logger.info(f"Lead archived in CRM: {lead_id}")
        return lead

    @staticmethod
    def get_lead(db: Session, lead_id: str) -> Lead:
        """Retrieve a lead from the CRM."""
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            raise ValueError(f"Lead {lead_id} not found")
        return lead

    @staticmethod
    def get_all_leads(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        status: str = None,
        classification: str = None,
    ) -> list[Lead]:
        """Get all leads with optional filtering."""
        query = db.query(Lead)
        if status:
            query = query.filter(Lead.status == status)
        if classification:
            query = query.filter(Lead.classification == classification)
        return query.order_by(Lead.created_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def count_leads(db: Session) -> int:
        """Count total leads."""
        return db.query(Lead).count()


crm_tool = CRMWriteTool()