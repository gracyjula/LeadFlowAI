"""Lead Enrichment Tool (Tool A) - Enriches lead data with company and buying signal information."""

import logging
import re
from typing import Optional
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)


class LeadEnrichmentTool:
    """
    Tool A: Lead Enrichment Tool
    
    Enriches lead data by gathering/simulating:
    - Company industry
    - Company size
    - Estimated revenue
    - Company website
    - Buying signals
    - Decision-maker status
    - Market segment
    """

    async def enrich(self, lead_data: dict) -> dict:
        """
        Enrich lead data using available information and LLM analysis.
        
        Args:
            lead_data: Dictionary containing lead information (name, email, job_title,
                      company_name, company_website, company_size, industry, message)
        
        Returns:
            Dictionary with enriched data
        """
        company_name = lead_data.get("company_name", "")
        company_website = lead_data.get("company_website", "")
        job_title = lead_data.get("job_title", "")
        company_size = lead_data.get("company_size", "")
        industry = lead_data.get("industry", "")
        message = lead_data.get("message", "")

        # Extract domain from website or email
        domain = self._extract_domain(company_website or lead_data.get("email", ""))

        # Use LLM for intelligent enrichment when possible
        try:
            enriched = await self._llm_enrich(lead_data)
        except Exception as e:
            logger.warning(f"LLM enrichment failed, using rule-based: {e}")
            enriched = self._rule_based_enrich(lead_data)

        # Always add domain if available
        if domain and not enriched.get("enriched_website"):
            enriched["enriched_website"] = f"https://{domain}"

        # Detect buying signals from message
        buying_signals = self._detect_buying_signals(message)
        if buying_signals:
            existing_signals = enriched.get("buying_signals", [])
            if isinstance(existing_signals, list):
                enriched["buying_signals"] = list(set(existing_signals + buying_signals))
            else:
                enriched["buying_signals"] = buying_signals

        # Determine decision maker status from job title
        enriched["decision_maker_status"] = self._is_decision_maker(job_title)

        return enriched

    async def _llm_enrich(self, lead_data: dict) -> dict:
        """Use LLM to enrich lead data."""
        system_prompt = """You are a B2B lead enrichment assistant. Analyze the lead information and provide enriched data.
Return a JSON object with these fields:
- enriched_industry: The most likely industry (SaaS, Technology, Finance, Healthcare, or other)
- enriched_company_size: Estimated company size (e.g., "1-10", "11-50", "51-200", "201-1000", "1000+")
- estimated_revenue: Estimated annual revenue range
- market_segment: Market segment (Enterprise, Mid-Market, SMB, Startup)
- buying_signals: Array of detected buying signals from the message
- confidence: Confidence level (high, medium, low)

Only use the information provided. Do not fabricate data. If insufficient data, mark confidence as low."""

        user_prompt = f"""Enrich this lead:
Company: {lead_data.get('company_name', 'N/A')}
Website: {lead_data.get('company_website', 'N/A')}
Industry (self-reported): {lead_data.get('industry', 'N/A')}
Company Size (self-reported): {lead_data.get('company_size', 'N/A')}
Job Title: {lead_data.get('job_title', 'N/A')}
Message: {lead_data.get('message', 'N/A')}"""

        result = await llm_service.structured_completion(system_prompt, user_prompt)
        return result

    def _rule_based_enrich(self, lead_data: dict) -> dict:
        """Fallback rule-based enrichment when LLM is unavailable."""
        industry = lead_data.get("industry", "")
        company_size = lead_data.get("company_size", "")
        job_title = lead_data.get("job_title", "")

        # Map common industries
        industry_map = {
            "saas": "SaaS",
            "tech": "Technology",
            "technology": "Technology",
            "finance": "Finance",
            "fintech": "Finance",
            "health": "Healthcare",
            "healthcare": "Healthcare",
            "medical": "Healthcare",
        }

        normalized_industry = industry.lower().strip() if industry else ""
        enriched_industry = None
        for key, value in industry_map.items():
            if key in normalized_industry:
                enriched_industry = value
                break

        # Estimate company size
        enriched_size = company_size if company_size else None

        # Determine market segment
        market_segment = "SMB"
        if enriched_size:
            size_num = 0
            try:
                size_num = int(re.sub(r"[^0-9]", "", enriched_size))
            except ValueError:
                pass
            if size_num > 1000:
                market_segment = "Enterprise"
            elif size_num > 200:
                market_segment = "Mid-Market"
            elif size_num > 50:
                market_segment = "Mid-Market"
            elif size_num > 10:
                market_segment = "SMB"
            else:
                market_segment = "Startup"

        return {
            "enriched_industry": enriched_industry,
            "enriched_company_size": enriched_size,
            "estimated_revenue": None,
            "market_segment": market_segment,
            "buying_signals": [],
            "confidence": "low",
        }

    def _detect_buying_signals(self, message: str) -> list:
        """Detect buying signals from lead message."""
        if not message:
            return []

        signals = []
        message_lower = message.lower()

        signal_patterns = [
            ("Requesting demo", ["demo", "demonstration", "see a demo", "book a demo"]),
            ("Evaluating solutions", ["evaluating", "considering", "looking for", "researching", "comparing"]),
            ("Looking for vendors", ["vendor", "provider", "solution", "tool", "platform"]),
            ("Budget discussions", ["budget", "pricing", "cost", "price", "investment", "roi"]),
            ("Timeline discussions", ["timeline", "urgent", "asap", "soon", "quarter", "this month", "this year"]),
            ("Specific feature request", ["integrate", "integration", "feature", "capability", "need"]),
            ("Competitor mention", ["switching from", "currently using", "migrate from", "replacing"]),
        ]

        for signal_name, patterns in signal_patterns:
            for pattern in patterns:
                if pattern in message_lower:
                    signals.append(signal_name)
                    break

        return signals

    def _is_decision_maker(self, job_title: str) -> bool:
        """Determine if the job title indicates a decision maker."""
        if not job_title:
            return False

        title_lower = job_title.lower()
        decision_maker_roles = [
            "cto", "ceo", "cfo", "coo", "cio", "cmo",
            "vp", "vice president",
            "director",
            "head of", "head ",
            "chief",
            "owner", "founder", "co-founder",
            "president",
            "senior manager", "sr manager",
            "lead",
        ]

        for role in decision_maker_roles:
            if role in title_lower:
                return True

        return False

    def _extract_domain(self, text: str) -> Optional[str]:
        """Extract domain from URL or email."""
        if not text:
            return None

        # Check for email pattern
        email_match = re.search(r"@([\w.-]+)", text)
        if email_match:
            return email_match.group(1)

        # Check for URL pattern
        url_match = re.search(r"(?:https?://)?(?:www\.)?([\w.-]+\.[a-z]{2,})", text)
        if url_match:
            return url_match.group(1)

        return None


enrichment_tool = LeadEnrichmentTool()