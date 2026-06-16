"""Multi-channel outreach message generator."""
from __future__ import annotations

from app.services import ai

CHANNELS = ["email", "whatsapp", "instagram", "facebook", "linkedin"]

_CHANNEL_BRIEF = {
    "email": "a professional cold email with a subject line, 90-130 words, clear CTA",
    "whatsapp": "a short, friendly WhatsApp message under 60 words, 1 emoji max",
    "instagram": "a casual Instagram DM under 45 words referencing their content",
    "facebook": "a polite Facebook page message under 60 words",
    "linkedin": "a professional LinkedIn connection message under 60 words",
}


DEFAULT_BRAND = "Kunonu Digital"


def _signature(brand: str) -> str:
    return f"— The team at {brand}"


def generate_message(lead, channel: str, service: str = "website development",
                     brand: str | None = None) -> dict:
    """Return {channel, subject, body, ai_generated}."""
    brand = brand or DEFAULT_BRAND
    brief = _CHANNEL_BRIEF.get(channel, _CHANNEL_BRIEF["email"])
    prompt = (
        f"Write {brief} to {lead.business_name}, a {lead.industry or lead.category} in "
        f"{lead.city or 'Tanzania'}. Goal: offer '{service}' to help them win more customers. "
        f"Personalize using: {lead.ai_summary or ''}. Sign as '{brand}'. "
        + ('Return JSON {"subject": "...", "body": "..."}.' if channel == "email"
           else 'Return JSON {"body": "..."}.')
    )

    def fallback() -> dict:
        from app.services.offering import is_website_service

        name = lead.business_name
        loc = lead.city or "Tanzania"
        cat = (lead.category or lead.industry or "business").lower()
        signoff = _signature(brand)
        website = is_website_service(service)
        # A short, service-aware hook reused across channels.
        hook = (
            "you don't have a website yet — we build fast sites + AI chatbots that bring in "
            "Google customers"
            if website
            else f"we help {cat}s like yours with {service} to win more customers and save time"
        )
        if channel == "email":
            pain = (
                f"I noticed you don't have a website yet, so customers searching Google for "
                f"{cat} in {loc} can't find you"
                if website
                else f"I think {service} could help you reach and serve more customers"
            )
            return {
                "subject": (
                    f"Helping {name} win more customers from Google" if website
                    else f"{service.capitalize()} for {name}"
                ),
                "body": (
                    f"Hi {name} team,\n\n"
                    f"I came across your {cat} in {loc} and loved what you're doing on social "
                    f"media — {pain}.\n\n"
                    f"We help Tanzanian {cat}s with {service}. Could I send over a quick example "
                    f"and a free plan tailored to {name}?\n\n{signoff}"
                ),
            }
        bodies = {
            "whatsapp": f"Hi {name}! 👋 Love your work in {loc}. {hook.capitalize()}. Mind if I share a quick example?",
            "instagram": f"Hey {name}! Your page is great — {hook}. Open to a quick look?",
            "facebook": f"Hello {name} team — {hook}. Could we share a free tailored plan?",
            "linkedin": f"Hi — I work with Tanzanian {cat}s like {name} on {service}. Would love to connect and share ideas.",
        }
        return {"body": bodies.get(channel, bodies["facebook"])}

    data, ai_gen = ai.generate_json(prompt, fallback)
    subject = data.get("subject") if channel == "email" else None
    return {"channel": channel, "subject": subject, "body": data.get("body", ""), "ai_generated": ai_gen}


def generate_all(lead, channels: list[str] | None = None, service: str = "website development",
                 brand: str | None = None) -> list[dict]:
    return [generate_message(lead, c, service, brand) for c in (channels or CHANNELS)]
