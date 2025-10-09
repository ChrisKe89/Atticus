"""Lightweight HTML shell for test and health checks."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

_HTML_RESPONSE = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>Atticus Admin Console</title>
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <style>
      body {
        font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        margin: 2rem;
        line-height: 1.5;
      }
      h1 {
        font-size: 1.75rem;
        margin-bottom: 0.5rem;
      }
      p {
        margin: 0;
        color: #475569;
      }
    </style>
  </head>
  <body>
    <h1>Atticus</h1>
    <p>The Atticus API is running. Use the Next.js frontend for the full experience.</p>
  </body>
</html>
"""


@router.get("/ui", response_class=HTMLResponse, include_in_schema=False)
async def ui_landing() -> str:
    """Serve a minimal HTML response that confirms the API is available."""

    return _HTML_RESPONSE
