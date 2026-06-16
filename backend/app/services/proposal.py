"""Customized proposal generator (structured sections)."""
from __future__ import annotations

from app.services import ai


def build_proposal(lead, service: str = "website development") -> tuple[dict, bool]:
    prompt = (
        f"Create a concise sales proposal for an agency pitching '{service}' to this Tanzanian "
        "business. Return JSON with keys: executive_summary (string), current_situation (string), "
        "recommended_solution (array of strings), expected_benefits (array of strings), "
        "estimated_timeline (object with phase1 and phase2 strings), call_to_action (string).\n\n"
        f"Service offered: {service}\n"
        f"Business: {lead.business_name}\n"
        f"Industry: {lead.industry or lead.category}\n"
        f"Location: {lead.city or lead.region or 'Tanzania'}\n"
        f"Summary: {lead.ai_summary or ''}"
    )

    def fallback() -> dict:
        from app.services.offering import is_website_service

        name = lead.business_name
        if is_website_service(service):
            return {
                "executive_summary": (
                    f"{name} has built an engaged social following but has no website, leaving "
                    f"revenue on the table from customers searching online. This proposal outlines "
                    f"a website, AI chatbot, and lead-generation system to capture that demand."
                ),
                "current_situation": (
                    f"{name} relies primarily on social media and word of mouth. It has no owned "
                    f"website, so it is hard to find on Google, cannot take online bookings, and "
                    f"has no automated way to capture or qualify leads."
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
                "estimated_timeline": {"phase1": "Website: 2–4 weeks", "phase2": "AI chatbot: 1 week"},
                "call_to_action": "Schedule a free 30-minute consultation to review a tailored plan.",
            }
        cat = (lead.category or lead.industry or "business").lower()
        return {
            "executive_summary": (
                f"{name} is a well-followed {cat} in {lead.city or 'Tanzania'} that could grow "
                f"faster with {service}. This proposal outlines how we'd implement {service} to "
                f"win more customers and run more efficiently."
            ),
            "current_situation": (
                f"{name} currently operates without {service}, relying on manual processes and "
                f"social media. That limits reach, efficiency, and the ability to scale."
            ),
            "recommended_solution": [
                f"Implement {service} tailored to a {cat}",
                "Integrate with their existing WhatsApp / social channels",
                "Set up tracking so impact is measurable",
                "Train the team and provide ongoing support",
            ],
            "expected_benefits": [
                f"More customers and revenue via {service}",
                "Time saved through automation",
                "Better customer experience and retention",
                "A measurable edge over competitors",
            ],
            "estimated_timeline": {"phase1": "Setup & rollout: 1–3 weeks", "phase2": "Optimization: ongoing"},
            "call_to_action": "Schedule a free 30-minute consultation to review a tailored plan.",
        }

    return ai.generate_json(prompt, fallback)
