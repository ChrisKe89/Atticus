import os

from openai import OpenAI

from atticus.config import load_settings

s = load_settings()
k = s.openai_api_key or os.getenv("OPENAI_API_KEY")


try:
    c = OpenAI(api_key=k)
    # Low-cost call: list models
    ms = c.models.list()
    print("models_count", len(getattr(ms, "data", []) or []))
except Exception as e:
    print("exc_type", type(e).__name__)
    print("exc", str(e)[:400])
