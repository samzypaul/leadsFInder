"""Test environment guard.

Runs before any test module (and before `app` is imported), forcing safe local settings so
the suite never touches the real database or burns live AI/search quota — even if a developer
has a populated `.env` with Neon/Gemini credentials sitting in the backend directory.
"""
import os

os.environ["DATABASE_URL"] = "sqlite:///./test_leadhunter.db"
os.environ["AI_PROVIDER"] = "fallback"      # never call a real model in tests
os.environ["GEMINI_API_KEY"] = ""
os.environ["OPENAI_API_KEY"] = ""
os.environ["GOOGLE_SEARCH_API_KEY"] = ""
os.environ["GOOGLE_SEARCH_CX"] = ""
os.environ["SCRAPER_MODE"] = "fallback"
os.environ["ADMIN_PASSWORD"] = "secret123"
os.environ.setdefault("SECRET_KEY", "test-secret")
