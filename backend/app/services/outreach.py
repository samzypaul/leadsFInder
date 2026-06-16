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


def _signature() -> str:
    return "— The team at Kunonu Digital"


def generate_message(lead, channel: str) -> dict:
    """Return {channel, subject, body, ai_generated}."""
    brief = _CHANNEL_BRIEF.get(channel, _CHANNEL_BRIEF["email"])
    prompt = (
        f"Write {brief} to {lead.business_name}, a {lead.industry or lead.category} in "
        f"{lead.city or 'Tanzania'}. Goal: offer a website + AI chatbot to win them more "
        f"customers from Google. Personalize using: {lead.ai_summary or ''}. "
        f"Sign as 'Kunonu Digital'. "
        + ('Return JSON {"subject": "...", "body": "..."}.' if channel == "email"
           else 'Return JSON {"body": "..."}.')
    )

    def fallback() -> dict:
        name = lead.business_name
        loc = lead.city or "Tanzania"
        cat = (lead.category or lead.industry or "business").lower()
        if channel == "email":
            return {
                "subject": f"Helping {name} win more customers from Google",
                "body": (
                    f"Hi {name} team,\n\n"
                    f"I came across your {cat} in {loc} and loved what you're doing on social "
                    f"media — but I noticed you don't have a website yet. That means customers "
                    f"searching Google for {cat} in {loc} can't find you, and you may be losing "
                    f"those enquiries to competitors.\n\n"
                    f"We build fast, mobile-first websites with an AI chatbot and WhatsApp "
                    f"booking — typically live in 2–4 weeks. Could I send over a quick example "
                    f"and a free plan tailored to {name}?\n\n{_signature()}"
                ),
            }
        bodies = {
            "whatsapp": (
                f"Hi {name}! 👋 Love your work in {loc}. We noticed you don't have a website yet "
                f"— we build sites + AI chatbots that bring in Google customers. Mind if I share "
                f"a quick example?"
            ),
            "instagram": (
                f"Hey {name}! Your page is great. Noticed there's no website linked — we help "
                f"{cat}s in {loc} get found on Google with a site + AI chatbot. Open to a quick look?"
            ),
            "facebook": (
                f"Hello {name} team — we help Tanzanian {cat}s turn social followers into Google "
                f"customers with a website + AI chatbot. Could we share a free tailored plan?"
            ),
            "linkedin": (
                f"Hi — I work with Tanzanian {cat}s like {name} to build websites + AI chatbots "
                f"that capture Google search demand. Would love to connect and share ideas."
            ),
        }
        return {"body": bodies.get(channel, bodies["facebook"])}

    if channel == "email":
        data, ai_gen = ai.generate_json(prompt, fallback)
        return {"channel": channel, "subject": data.get("subject"),
                "body": data.get("body", ""), "ai_generated": ai_gen}
    data, ai_gen = ai.generate_json(prompt, fallback)
    return {"channel": channel, "subject": None, "body": data.get("body", ""), "ai_generated": ai_gen}


def generate_all(lead, channels: list[str] | None = None) -> list[dict]:
    return [generate_message(lead, c) for c in (channels or CHANNELS)]
