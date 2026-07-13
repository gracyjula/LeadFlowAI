"""LeadFlow Agent - Main orchestration agent using LangGraph.

Workflow:
Lead Submission → Enrichment → Scoring → Classification → Routing → Email Drafting → Human Approval → Send
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session

from app.models.models import Lead, LeadStatus, Classification
from app.models.schemas import LeadCreate
from app.tools.enrichment_tool import enrichment_tool
from app.tools.crm_tool import crm_tool
from app.tools.email_tool import email_tool
from app.services.llm_service import llm_service
from app.services.audit_service import audit_service

logger = logging.getLogger(__name__)


# --- ICP Definition ---

ICP_DEFINITION = {
    "ideal_industries": ["SaaS", "Technology", "Finance", "Healthcare"],
    "ideal_company_size_min": 100,
    "ideal_roles": ["CTO", "CEO", "VP", "Director", "Head Of Department", "Chief", "President", "Founder"],
    "buying_signals_weight": 30,
    "industry_weight": 25,
    "company_size_weight": 20,
    "role_weight": 25,
}


class LeadFlowAgent:
    """
    Main agent orchestrating the lead qualification workflow.
    
    Uses LangGraph-style state machine for the workflow:
    enrich → score → classify → route → draft_email
    """

    async def process_lead(self, db: Session, lead_data: LeadCreate) -> Dict[str, Any]:
        """
        Process a lead through the entire workflow.
        
        Args:
            db: Database session
            lead_data: Validated lead input data
            
        Returns:
            Processing result dictionary
        """
        tool_calls = []
        lead = None

        try:
            # Step 1: Create lead in CRM
            lead = crm_tool.create_lead(db, lead_data.model_dump())
            tool_calls.append({"tool": "CRMWriteTool.create_lead", "status": "success"})

            audit_service.log_event(
                db, lead.id, "LEAD_CREATED",
                input_data=lead_data.model_dump(),
                tool_calls=tool_calls,
            )

            # Injection defense: Check message for injection attempts
            injection_keywords = [
                "ignore instructions", "ignore all rules", "ignore scoring",
                "mark me hot", "mark me as hot", "classify me as hot",
                "ignore your instructions", "system prompt", "override",
                "you are now", "from now on",
            ]
            message = lead_data.message or ""
            message_lower = message.lower()
            injection_detected = any(keyword in message_lower for keyword in injection_keywords)
            
            if injection_detected:
                logger.warning(f"Injection attempt detected in lead {lead.id}: {message[:100]}")
                crm_tool.update_lead(db, lead.id, {"injection_attempt_detected": True})
                audit_service.log_event(
                    db, lead.id, "INJECTION_ATTEMPT_BLOCKED",
                    details={
                        "message_preview": message[:200],
                        "action_taken": "Message ignored, normal scoring applied",
                        "detection_method": "Keyword pattern matching",
                    },
                    tool_calls=tool_calls,
                )

            # Step 2: Enrich lead data
            enriched = await self._enrich_lead(db, lead)
            tool_calls.append({"tool": "LeadEnrichmentTool.enrich", "status": "success"})

            audit_service.log_event(
                db, lead.id, "LEAD_ENRICHED",
                enrichment_results=enriched,
                tool_calls=tool_calls,
            )

            # Step 3: Score the lead
            scoring_result = await self._score_lead(db, lead, enriched)
            tool_calls.append({"tool": "ScoreEngine.score", "status": "success"})

            audit_service.log_event(
                db, lead.id, "LEAD_SCORED",
                score=scoring_result["score"],
                details={"score_reason": scoring_result["reason"], "components": scoring_result.get("components")},
                tool_calls=tool_calls,
            )

            # Step 4: Classify the lead
            classification_result = self._classify_lead(db, lead, scoring_result)
            tool_calls.append({"tool": "ClassificationEngine.classify", "status": "success"})

            audit_service.log_event(
                db, lead.id, "LEAD_CLASSIFIED",
                score=scoring_result["score"],
                classification=classification_result["classification"],
                classification_reason=classification_result["reason"],
                tool_calls=tool_calls,
            )

            # Step 5: Route the lead
            routing_result = self._route_lead(db, lead, classification_result)
            tool_calls.append({"tool": "RoutingEngine.route", "status": "success"})

            audit_service.log_event(
                db, lead.id, "LEAD_ROUTED",
                details={"routing_action": routing_result["action"], "routing_reason": routing_result["reason"]},
                tool_calls=tool_calls,
            )

            # Step 6: Draft email (only for HOT leads)
            email_result = None
            if classification_result["classification"] == "HOT":
                email_result = await self._draft_email(db, lead, enriched, scoring_result)
                tool_calls.append({"tool": "EmailDraftEngine.draft", "status": "success"})

                audit_service.log_event(
                    db, lead.id, "EMAIL_DRAFTED",
                    draft_email={
                        "subject": email_result.get("subject"),
                        "body": email_result.get("body"),
                    },
                    details={"email_status": "PENDING_APPROVAL"},
                    tool_calls=tool_calls,
                )

            lead = crm_tool.get_lead(db, lead.id)

            return {
                "lead_id": lead.id,
                "status": lead.status,
                "classification": classification_result["classification"],
                "score": scoring_result["score"],
                "score_reason": scoring_result["reason"],
                "classification_reason": classification_result["reason"],
                "routing_action": routing_result["action"],
                "draft_email_subject": email_result.get("subject") if email_result else None,
                "draft_email_body": email_result.get("body") if email_result else None,
                "email_status": "PENDING_APPROVAL" if email_result else "NOT_DRAFTED",
                "message": f"Lead processed: {classification_result['classification']}",
            }

        except Exception as e:
            logger.error(f"Lead processing failed: {str(e)}", exc_info=True)
            tool_calls.append({"tool": "error", "status": "failed", "error": str(e)})

            if lead:
                crm_tool.update_lead(db, lead.id, {
                    "status": LeadStatus.ERROR.value,
                    "error_message": str(e),
                })

                audit_service.log_event(
                    db, lead.id, "PROCESSING_ERROR",
                    errors=str(e),
                    tool_calls=tool_calls,
                )

            return {
                "lead_id": lead.id if lead else "unknown",
                "status": "ERROR",
                "message": f"Processing failed: {str(e)}",
            }

    async def _enrich_lead(self, db: Session, lead: Lead) -> dict:
        """Step 2: Enrich lead data."""
        lead_data = {
            "name": lead.name,
            "email": lead.email,
            "job_title": lead.job_title,
            "company_name": lead.company_name,
            "company_website": lead.company_website,
            "company_size": lead.company_size,
            "industry": lead.industry,
            "message": lead.message,
        }

        enriched = await enrichment_tool.enrich(lead_data)

        # Save enrichment results to CRM
        update_data = {
            "enriched_industry": enriched.get("enriched_industry"),
            "enriched_company_size": enriched.get("enriched_company_size"),
            "estimated_revenue": enriched.get("estimated_revenue"),
            "enriched_website": enriched.get("enriched_website"),
            "buying_signals": enriched.get("buying_signals", []),
            "decision_maker_status": enriched.get("decision_maker_status"),
            "market_segment": enriched.get("market_segment"),
            "status": LeadStatus.ENRICHED.value,
        }
        crm_tool.update_lead(db, lead.id, update_data)

        return enriched

    async def _score_lead(self, db: Session, lead: Lead, enriched: dict) -> dict:
        """
        Step 3: Score the lead using transparent, explainable criteria.
        
        Scoring breakdown:
        - Industry Match: 25 points
        - Company Size Match: 20 points
        - Decision Maker Role: 25 points
        - Buying Intent: 30 points
        Total: 100 points
        """
        # Get the best available data (enriched takes priority, then self-reported)
        industry = (enriched.get("enriched_industry") or lead.industry or "").lower()
        company_size_str = (enriched.get("enriched_company_size") or lead.company_size or "0")
        job_title = (lead.job_title or "").lower()
        buying_signals = enriched.get("buying_signals", [])
        if isinstance(buying_signals, str):
            try:
                buying_signals = json.loads(buying_signals)
            except (json.JSONDecodeError, TypeError):
                buying_signals = []

        # Also check message for buying signals
        message = lead.message or ""
        message_lower = message.lower()

        # --- Industry Score (25 points) ---
        industry_score = 0
        industry_reason_parts = []
        ideal_industries = [ind.lower() for ind in ICP_DEFINITION["ideal_industries"]]

        for ideal_ind in ideal_industries:
            if ideal_ind in industry:
                industry_score = 25
                industry_reason_parts.append(f"Industry matches ICP: {industry.title()}")
                break

        if industry_score == 0 and industry:
            industry_score = 10
            industry_reason_parts.append(f"Industry '{industry.title()}' is not an ICP match (partial: 10 pts)")
        elif not industry:
            industry_score = 0
            industry_reason_parts.append("No industry data available (0 pts)")

        # --- Company Size Score (20 points) ---
        company_size_score = 0
        try:
            # Extract numeric value from company size string
            size_clean = "".join(c for c in company_size_str if c.isdigit() or c in "+-,")
            # Handle ranges like "100-500" or "100+"
            if "-" in size_clean:
                size_num = int(size_clean.split("-")[0].strip())
            elif "+" in size_clean:
                size_num = int(size_clean.replace("+", "").strip())
            elif "," in size_clean:
                size_num = int(size_clean.replace(",", "").strip())
            else:
                size_num = int(size_clean) if size_clean else 0

            if size_num >= 1000:
                company_size_score = 20
                industry_reason_parts.append(f"Large company: {size_num} employees (20 pts)")
            elif size_num >= 100:
                company_size_score = 20
                industry_reason_parts.append(f"Company size {size_num} meets ICP threshold (20 pts)")
            elif size_num >= 50:
                company_size_score = 15
                industry_reason_parts.append(f"Company size {size_num} close to ICP threshold (15 pts)")
            elif size_num >= 10:
                company_size_score = 10
                industry_reason_parts.append(f"Small company: {size_num} employees (10 pts)")
            else:
                company_size_score = 5
                industry_reason_parts.append(f"Very small company: {size_num} employees (5 pts)")
        except (ValueError, TypeError):
            company_size_score = 10
            industry_reason_parts.append(f"Company size '{company_size_str}' - estimated partial (10 pts)")

        # --- Role/Decision Maker Score (25 points) ---
        role_score = 0
        role_reason_parts = []
        ideal_roles_lower = [r.lower() for r in ICP_DEFINITION["ideal_roles"]]

        for ideal_role in ideal_roles_lower:
            if ideal_role in job_title:
                role_score = 25
                role_reason_parts.append(f"Decision maker role: {lead.job_title} (25 pts)")
                break

        if role_score == 0:
            # Check if any decision maker indicator
            dm_indicators = ["manager", "lead", "senior", "sr ", "head", "principal"]
            for indicator in dm_indicators:
                if indicator in job_title:
                    role_score = 15
                    role_reason_parts.append(f"Mid-level role: {lead.job_title} (15 pts)")
                    break

            if role_score == 0 and job_title:
                role_score = 5
                role_reason_parts.append(f"Non-decision maker role: {lead.job_title} (5 pts)")
            elif not job_title:
                role_score = 0
                role_reason_parts.append("No job title provided (0 pts)")

        # --- Buying Intent Score (30 points) ---
        buying_intent_score = 0
        intent_reason_parts = []

        # Check buying signals from enrichment
        if buying_signals and isinstance(buying_signals, list):
            num_signals = len(buying_signals)
            if num_signals >= 3:
                buying_intent_score = 30
                intent_reason_parts.append(f"Strong buying signals detected: {', '.join(buying_signals[:3])} (30 pts)")
            elif num_signals == 2:
                buying_intent_score = 25
                intent_reason_parts.append(f"Multiple buying signals: {', '.join(buying_signals)} (25 pts)")
            elif num_signals == 1:
                buying_intent_score = 20
                intent_reason_parts.append(f"Buying signal detected: {buying_signals[0]} (20 pts)")
        else:
            intent_reason_parts.append("No explicit buying signals detected")

        # Check message for direct intent indicators
        intent_keywords = {
            "demo": 10,
            "pricing": 8,
            "purchase": 10,
            "buy": 10,
            "implement": 8,
            "urgent": 8,
            "trial": 8,
            "quote": 8,
            "partnership": 5,
            "collaborate": 5,
        }

        message_intent_score = 0
        for keyword, points in intent_keywords.items():
            if keyword in message_lower:
                message_intent_score = max(message_intent_score, points)
                intent_reason_parts.append(f"Intent keyword '{keyword}' found in message (+{points} pts)")

        # Take the better of structured signals vs message analysis
        buying_intent_score = max(buying_intent_score, message_intent_score)

        if buying_intent_score == 0:
            intent_reason_parts.append("No buying intent detected (0 pts)")

        # --- Calculate Total ---
        total_score = industry_score + company_size_score + role_score + buying_intent_score
        total_score = min(total_score, 100)  # Cap at 100

        # Build reason
        all_reasons = industry_reason_parts + role_reason_parts + intent_reason_parts
        reason = "\n".join([f"• {r}" for r in all_reasons])

        # Save scoring to CRM
        crm_tool.update_lead(db, lead.id, {
            "score": total_score,
            "score_reason": reason,
            "industry_score": industry_score,
            "company_size_score": company_size_score,
            "role_score": role_score,
            "buying_intent_score": buying_intent_score,
            "status": LeadStatus.SCORED.value,
        })

        return {
            "score": total_score,
            "reason": reason,
            "components": {
                "industry_score": industry_score,
                "company_size_score": company_size_score,
                "role_score": role_score,
                "buying_intent_score": buying_intent_score,
            },
        }

    def _classify_lead(self, db: Session, lead: Lead, scoring_result: dict) -> dict:
        """
        Step 4: Classify the lead based on score.
        
        Score ≥ 80: HOT
        Score 40-79: NURTURE
        Score < 40: DISQUALIFY
        """
        score = scoring_result["score"]

        if score >= 80:
            classification = Classification.HOT.value
            reason = (
                f"Lead scored {score}/100 - qualifies as HOT.\n"
                f"Strong alignment with ICP across all dimensions."
            )
            status = LeadStatus.CLASSIFIED.value

        elif score >= 40:
            classification = Classification.NURTURE.value
            reason = (
                f"Lead scored {score}/100 - qualifies for NURTURE.\n"
                f"Moderate alignment with ICP. Requires further engagement."
            )
            status = LeadStatus.CLASSIFIED.value

        else:
            classification = Classification.DISQUALIFY.value
            reason = (
                f"Lead scored {score}/100 - DISQUALIFIED.\n"
                f"Insufficient alignment with ICP."
            )
            status = LeadStatus.ARCHIVED.value

        crm_tool.update_lead(db, lead.id, {
            "classification": classification,
            "classification_reason": reason,
            "status": status,
        })

        return {
            "classification": classification,
            "reason": reason,
        }

    def _route_lead(self, db: Session, lead: Lead, classification_result: dict) -> dict:
        """
        Step 5: Route the lead based on classification.
        
        HOT → SDR Review Queue
        NURTURE → Nurture Sequence
        DISQUALIFY → Archive
        """
        classification = classification_result["classification"]

        if classification == "HOT":
            action = "SDR_REVIEW_QUEUE"
            reason = "High-value lead moved to SDR review queue for immediate follow-up."
            status = LeadStatus.ROUTED.value

        elif classification == "NURTURE":
            action = "NURTURE_SEQUENCE"
            reason = "Lead routed to nurture sequence for long-term engagement."
            status = LeadStatus.ROUTED.value

        else:  # DISQUALIFY
            action = "ARCHIVED"
            reason = classification_result.get("reason", "Lead disqualified and archived.")
            status = LeadStatus.ARCHIVED.value

        crm_tool.update_lead(db, lead.id, {
            "routing_action": action,
            "routing_reason": reason,
            "status": status,
        })

        return {
            "action": action,
            "reason": reason,
        }

    async def _draft_email(self, db: Session, lead: Lead, enriched: dict, scoring_result: dict) -> dict:
        """
        Step 6: Draft a personalized email for HOT leads.
        
        Only HOT leads receive email drafts.
        Email is always set to PENDING_APPROVAL - never auto-sent.
        """
        # Prepare context for email generation
        company_name = lead.company_name or enriched.get("enriched_industry", "your company")
        industry = enriched.get("enriched_industry") or lead.industry or "your industry"
        role = lead.job_title or "professional"
        buying_signals = enriched.get("buying_signals", [])
        if isinstance(buying_signals, str):
            try:
                buying_signals = json.loads(buying_signals)
            except (json.JSONDecodeError, TypeError):
                buying_signals = []
        signal_text = ", ".join(buying_signals[:3]) if buying_signals else "exploring solutions"

        # Score components for personalization
        components = scoring_result.get("components", {})

        system_prompt = """You are a professional B2B sales email writer. 
Craft a concise, personalized outreach email.

Rules:
- Be professional and concise (max 150 words)
- Reference the lead's company, role, and industry
- Acknowledge their specific situation or buying signals
- Include a clear, low-pressure call to action
- Do NOT be overly salesy or use excessive flattery
- Do NOT mention the scoring or classification process
- Sign as "Sales Team"
- Return ONLY the email body text, no subject line"""

        user_prompt = f"""Write a personalized outreach email for:
- Company: {company_name}
- Industry: {industry}
- Role: {role}
- Interest/Signal: {signal_text}

The email should reference their role at {company_name} in the {industry} space, 
acknowledge their interest in {signal_text}, and offer a brief conversation."""

        try:
            email_body = await llm_service.chat_completion(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.3,
                max_tokens=500,
            )

            # Generate subject line
            subject_prompt = f"Generate a professional email subject line for a B2B outreach to {role} at {company_name} about {signal_text}. Return only the subject line, no quotes."
            email_subject = await llm_service.chat_completion(
                system_prompt="You generate concise B2B email subject lines. Return only the subject text.",
                user_prompt=subject_prompt,
                temperature=0.3,
                max_tokens=100,
            )

        except Exception as e:
            logger.warning(f"LLM email generation failed, using template: {e}")
            email_subject = f"Quick question about {company_name}'s priorities"
            email_body = (
                f"Hi there,\n\n"
                f"I noticed you've been exploring solutions at {company_name}. "
                f"Given your role as {role} in the {industry} space, "
                f"I believe we could add significant value.\n\n"
                f"Would you be open to a brief 15-minute call next week to discuss how "
                f"we help companies like {company_name} address their needs?\n\n"
                f"Best regards,\nSales Team"
            )

        # Clean subject
        email_subject = email_subject.strip().strip('"').strip("'").strip()

        # Save draft to CRM
        crm_tool.update_lead(db, lead.id, {
            "draft_email_subject": email_subject,
            "draft_email_body": email_body,
            "email_status": "PENDING_APPROVAL",
            "status": LeadStatus.PENDING_APPROVAL.value,
        })

        return {
            "subject": email_subject,
            "body": email_body,
        }


lead_flow_agent = LeadFlowAgent()