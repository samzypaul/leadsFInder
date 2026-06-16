"""AI enrichment: business summary, opportunity analysis, marketing strategy.

Each function returns a value plus an `ai_generated` flag, and degrades gracefully to a
deterministic template when no model key is configured.
"""
from __future__ import annotations

from app.services import ai


def _ctx(lead) -> str:
    parts = [
        f"Business name: {lead.business_name}",
        f"Industry/category: {lead.industry or lead.category or 'unknown'}",
        f"Location: {', '.join(filter(None, [lead.city, lead.region, lead.country]))}",
        f"Bio/description: {lead.description or 'n/a'}",
        f"Followers: {lead.followers or 'n/a'}, Reviews: {lead.reviews_count or 'n/a'}, "
        f"Rating: {lead.rating or 'n/a'}",
        f"Channels: IG={bool(lead.instagram_url)}, FB={bool(lead.facebook_url)}, "
        f"GBP={bool(lead.google_business_url)}, Website=None",
    ]
    return "\n".join(parts)


def business_summary(lead) -> tuple[str, bool]:
    prompt = (
        "Write a single concise sentence (max 40 words) describing this Tanzanian business "
        "for a sales rep. Be factual, no fluff.\n\n" + _ctx(lead)
    )

    def fallback() -> str:
        cat = (lead.category or lead.industry or "business").lower()
        loc = lead.city or lead.region or "Tanzania"
        return (
            f"{lead.business_name} is a {cat} based in {loc} that currently reaches customers "
            f"through social media but has no website of its own."
        )

    return ai.generate_text(prompt, fallback)


def opportunity_analysis(lead, service: str = "website development") -> tuple[dict, bool]:
    from app.services.offering import is_website_service

    prompt = (
        f"List 4-6 specific reasons (short phrases) why this business would benefit from "
        f"'{service}' and is currently missing out without it. Return JSON: "
        '{"reasons": ["..."]}.\n\n' + _ctx(lead)
    )

    def fallback() -> dict:
        if is_website_service(service):
            reasons = [
                "No owned online presence — fully dependent on social platforms",
                "Losing leads from Google Search (no site to rank or be found)",
                "No online booking or enquiry capability",
                "No structured customer inquiry funnel",
                "Competitors in the same category already have websites",
            ]
            if lead.reviews_count:
                reasons.append("Strong reviews not showcased on an owned, conversion page")
            return {"reasons": reasons}
        # Generic, service-aware opportunity reasons.
        cat = (lead.category or lead.industry or "business").lower()
        return {"reasons": [
            f"No {service} in place — likely handled manually or not at all",
            f"Competing {cat}s adopting {service} are pulling ahead",
            f"Missed efficiency and revenue without {service}",
            f"Strong social audience ({lead.followers or 'an engaged following'}) "
            f"under-monetised without {service}",
            f"Customer demand not captured or automated without {service}",
        ]}

    return ai.generate_json(prompt, fallback)


def marketing_strategy(lead) -> tuple[dict, bool]:
    prompt = (
        "Produce a personalized digital strategy for this business as JSON with keys "
        '"website", "ai", "marketing", each an array of 3-5 concrete bullet actions.\n\n'
        + _ctx(lead)
    )

    def fallback() -> dict:
        return {
            "website": [
                "Modern responsive website",
                "SEO optimization for local search",
                "Google Maps integration",
                "WhatsApp click-to-chat integration",
                "Online booking / enquiry form",
            ],
            "ai": [
                "AI chatbot for instant replies",
                "Automated customer support",
                "Lead qualification bot",
                "FAQ automation",
            ],
            "marketing": [
                "Google Business Profile optimization",
                "SEO content for Tanzania-specific keywords",
                "Social media automation",
                "Email marketing to past customers",
            ],
        }

    return ai.generate_json(prompt, fallback)
