import os

from openai import OpenAI

from atticus.config import load_settings

s = load_settings()
k = s.openai_api_key or os.getenv("OPENAI_API_KEY")
try:
    c = OpenAI(api_key=k)
    e = c.embeddings.create(model="text-embedding-3-large", input=["hello"])
    print("embed_len", len(e.data[0].embedding))
except Exception as e:
    print("embed_error", type(e).__name__, str(e)[:300])
try:
    r = c.responses.create(model=s.generation_model, input=[{"role": "user", "content": "Hi"}])
    print("responses_ok", bool(getattr(r, "output", None)))
except Exception as e:
    print("responses_error", type(e).__name__, str(e)[:300])
