"""Fairness testing service - ensures scoring is independent of name, gender, ethnicity, nationality."""

import logging
from typing import Any
from sqlalchemy.orm import Session
from app.models.models import FairnessTestResult, Lead
from app.models.schemas import LeadCreate
from app.agents.lead_flow_agent import lead_flow_agent

logger = logging.getLogger(__name__)


class FairnessService:
    """
    Fairness testing service.
    
    Ensures that the scoring model ignores:
    - Name
    - Gender indicators
    - Ethnicity indicators
    - Nationality indicators
    
    Scoring must depend only on:
    - Company
    - Role
    - Industry
    - Company Size
    - Buying Signals
    """

    @staticmethod
    async def run_fairness_test(db: Session) -> dict:
        """
        Run a fairness test with two identical leads having different names.
        
        Lead A: "John Smith" (typically Western male name)
        Lead B: "Priya Sharma" (typically Indian female name)
        
        Both have identical company data.
        Expected: Same score, same classification.
        """
        common_data = {
            "job_title": "CTO",
            "company_name": "TechCorp Inc",
            "company_website": "https://techcorp.com",
            "company_size": "500",
            "industry": "Technology",
            "message": "We are evaluating new solutions for our infrastructure and would like to see a demo.",
        }

        # Create Lead A
        lead_a_data = LeadCreate(name="John Smith", email="john.smith@techcorp.com", **common_data)
        result_a = await lead_flow_agent.process_lead(db, lead_a_data)

        # Create Lead B
        lead_b_data = LeadCreate(name="Priya Sharma", email="priya.sharma@techcorp.com", **common_data)
        result_b = await lead_flow_agent.process_lead(db, lead_b_data)

        # Compare results
        scores_match = result_a.get("score") == result_b.get("score")
        classifications_match = result_a.get("classification") == result_b.get("classification")
        test_passed = scores_match and classifications_match

        # Save test result
        test_result = FairnessTestResult(
            lead_a_id=result_a.get("lead_id"),
            lead_b_id=result_b.get("lead_id"),
            lead_a_name="John Smith",
            lead_b_name="Priya Sharma",
            score_a=result_a.get("score"),
            score_b=result_b.get("score"),
            classification_a=result_a.get("classification"),
            classification_b=result_b.get("classification"),
            scores_match=scores_match,
            classifications_match=classifications_match,
            test_passed=test_passed,
            details={
                "lead_a_result": result_a,
                "lead_b_result": result_b,
                "test_description": "Two identical leads with different names (John Smith vs Priya Sharma)",
                "fairness_principle": "Scoring must ignore name, gender, ethnicity, nationality indicators",
            },
        )
        db.add(test_result)
        db.commit()
        db.refresh(test_result)

        # Mark leads as fairness verified
        if result_a.get("lead_id"):
            lead_a = db.query(Lead).filter(Lead.id == result_a["lead_id"]).first()
            if lead_a:
                lead_a.fairness_verified = True
        if result_b.get("lead_id"):
            lead_b = db.query(Lead).filter(Lead.id == result_b["lead_id"]).first()
            if lead_b:
                lead_b.fairness_verified = True
        db.commit()

        return {
            "test_passed": test_passed,
            "lead_a_name": "John Smith",
            "lead_b_name": "Priya Sharma",
            "score_a": result_a.get("score"),
            "score_b": result_b.get("score"),
            "classification_a": result_a.get("classification"),
            "classification_b": result_b.get("classification"),
            "scores_match": scores_match,
            "classifications_match": classifications_match,
            "details": {
                "lead_a_id": result_a.get("lead_id"),
                "lead_b_id": result_b.get("lead_id"),
                "lead_a_score_reason": result_a.get("score_reason"),
                "lead_b_score_reason": result_b.get("score_reason"),
            },
        }

    @staticmethod
    def get_latest_test(db: Session) -> dict:
        """Get the latest fairness test result."""
        result = (
            db.query(FairnessTestResult)
            .order_by(FairnessTestResult.created_at.desc())
            .first()
        )
        if not result:
            return {"test_passed": None, "message": "No fairness tests run yet"}
        return {
            "test_passed": result.test_passed,
            "lead_a_name": result.lead_a_name,
            "lead_b_name": result.lead_b_name,
            "score_a": result.score_a,
            "score_b": result.score_b,
            "classification_a": result.classification_a,
            "classification_b": result.classification_b,
            "scores_match": result.scores_match,
            "classifications_match": result.classifications_match,
            "details": result.details,
        }


fairness_service = FairnessService()