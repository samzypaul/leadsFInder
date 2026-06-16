"""Customized proposal generator (structured sections)."""
from __future__ import annotations

from app.services import ai


def build_proposal(lead) -> tuple[dict, bool]:
    prompt = (
        "Create a concise sales proposal for a web/AI/automation agency pitching this Tanzanian "
        "business. Return JSON with keys: executive_summary (string), current_situation (string), "
        "recommended_solution (array of strings), expected_benefits (array of strings), "
        "estimated_timeline (object with website and chatbot strings), call_to_action (string).\n\n"
        f"Business: {lead.business_name}\n"
        f"Industry: {lead.industry or lead.category}\n"
        f"Location: {lead.city or lead.region or 'Tanzania'}\n"
        f"Summary: {lead.ai_summary or ''}"
    )

    def fallback() -> dict:
        name = lead.business_name
        return {
            "executive_summary": (
                f"{name} has built an engaged social following but has no website, leaving "
                f"revenue on the table from customers searching online. This proposal outlines a "
                f"website, AI chatbot, and lead-generation system to capture that demand."
            ),
            "current_situation": (
                f"{name} relies primarily on social media (Instagram/Facebook) and word of mouth. "
                f"It has no owned website, so it is hard to find on Google, cannot take online "
                f"bookings/enquiries, and has no automated way to capture or qualify leads."
            ),
            "recommended_solution": [
                "Modern, mobile-first website with SEO foundations",
                "AI chatbot for instant customer support and lead qualification",
                "On-page SEO + Google Business Profile optimization",
                "Analytics and conversion tracking",
                "Integrated lead-generation system (forms + WhatsApp)",
            ],
            "expected_benefits": [
                "More customer inquiries from Google search",
                "Better online credibility and trust",
                "Higher Google visibility for local searches",
                "Automated, 24/7 customer engagement",
            ],
            "estimated_timeline": {
                "website": "Website: 2–4 weeks",
                "chatbot": "AI chatbot: 1 week",
            },
            "call_to_action": "Schedule a free 30-minute consultation to review a tailored plan.",
        }

    return ai.generate_json(prompt, fallback)
