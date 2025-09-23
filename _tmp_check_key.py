import os

from atticus.config import load_settings

s = load_settings()
k = s.openai_api_key or os.getenv("OPENAI_API_KEY")
print("present", bool(k))
print("len", len(k) if k else None)
if k:
    print("starts_ends_ws", k[:1].isspace(), k[-1:].isspace())
    print("prefix_suffix", (k[:10] if len(k) > 10 else k) + "...", k[-4:])
    print(
        "has_quotes", k.startswith('"') or k.endswith('"') or k.startswith("'") or k.endswith("'")
    )
