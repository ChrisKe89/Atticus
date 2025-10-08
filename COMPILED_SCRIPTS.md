# Compiled Scripts

## Makefile

```makefile
# Makefile — Atticus
.PHONY: env ingest eval api e2e openapi smtp-test smoke test test.unit test.api lint format typecheck quality web-build web-start web-lint web-typecheck web-dev app-dev help \
        db.up db.down db.migrate db.seed db.verify seed web-test web-e2e web-audit

PYTHON ?= python
XDIST_AVAILABLE := $(shell $(PYTHON) -c "import importlib.util; print(1 if importlib.util.find_spec('xdist') else 0)")
PYTEST_PARALLEL := $(if $(filter 1,$(XDIST_AVAILABLE)),-n auto,)

DB_SERVICE ?= postgres
PGVECTOR_DIMENSION ?= 3072
PGVECTOR_LISTS ?= 100

env:
	$(PYTHON) scripts/generate_env.py

smtp-test:
	$(PYTHON) scripts/smtp_test.py

help:
	@echo "Available targets:"
	@python scripts/list_make_targets.py $(MAKEFILE_LIST)

api:
	$(PYTHON) -m uvicorn api.main:app --reload --port 8000


web-dev:
	@echo "Launching Next.js UI on http://localhost:3000 (expects API on :8000)"
	npm run dev

app-dev:
	@echo "Alias for web-dev; launching Next.js UI"
	$(MAKE) web-dev

db.up:
	docker compose up -d $(DB_SERVICE)

db.down:
	docker compose stop $(DB_SERVICE)

db.migrate:
	npm run prisma:generate
	npm run db:migrate

db.verify:
	$(PYTHON) scripts/db_verify.py

db.seed:
	npm run db:seed

ingest:
	$(PYTHON) scripts/ingest_cli.py

seed:
	$(PYTHON) scripts/make_seed.py

eval:
	$(PYTHON) scripts/eval_run.py

openapi:
	$(PYTHON) scripts/generate_api_docs.py

smoke:
	PYTHONPATH=. $(PYTHON) scripts/test_health.py

test.unit:
	PYTHONPATH=. pytest $(PYTEST_PARALLEL) --maxfail=1 --disable-warnings \
	tests/test_hashing.py \
	tests/test_config_reload.py \
	tests/test_mailer.py \
	tests/test_chunker.py \
	tests/test_seed_manifest.py \
	tests/test_eval_runner.py

test.api:
	PYTHONPATH=. pytest $(PYTEST_PARALLEL) --maxfail=1 --disable-warnings \
	       tests/test_chat_route.py \
	       tests/test_contact_route.py \
	       tests/test_error_schema.py \
	       tests/test_ui_route.py

test:
	PYTHONPATH=. pytest $(PYTEST_PARALLEL) --maxfail=1 --disable-warnings \
	       --cov=atticus --cov=api --cov=retriever \
	       --cov-report=term-missing --cov-fail-under=90

web-test:
	npm run test:unit

web-e2e:
	npm run test:e2e

e2e: env ingest eval
	$(PYTHON) scripts/e2e_smoke.py

# Local quality gates (mirror CI)
lint:
	ruff check .
	ruff format --check .

format:
	ruff format .
	ruff check . --fix

typecheck:
	mypy atticus api ingest retriever eval

quality: lint typecheck test web-lint web-typecheck web-build web-audit

web-build:
	npm run build

web-start:
	npm run start

web-lint:
	npm run lint

web-typecheck:
	npm run typecheck

web-audit:
	npm run audit:ts
	npm run audit:icons
	npm run audit:routes
	npm run audit:py
```

## docker-compose.yml

```yaml
services:
  postgres:
    image: pgvector/pgvector:pg16
    container_name: atticus-postgres
    restart: unless-stopped
    env_file: .env
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-atticus}
      POSTGRES_USER: ${POSTGRES_USER:-atticus}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-atticus}
      VECTOR_INDEX_MAX_DIMENSIONS: 4096
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  api:
    build: ./api
    container_name: atticus-api
    env_file: .env
    depends_on:
      - postgres
    volumes:
      - ./content:/app/content:ro
      - indices:/app/indices
      - logs:/app/logs
    ports:
      - "8000:8000"
    command: ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 10s
      timeout: 3s
      retries: 5

  nginx:
    build: ./nginx
    container_name: atticus-nginx
    depends_on:
      api:
        condition: service_healthy
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/certs:/etc/nginx/certs:ro
    healthcheck:
      test: ["CMD", "nginx", "-t"]
      interval: 30s
      timeout: 5s
      retries: 3

volumes:
  indices:
  logs:
  postgres_data:
```

## combine-code.ps1

```powershell
<#
Combine relevant source files into a single Markdown bundle.

Usage examples:
  pwsh -NoProfile -ExecutionPolicy Bypass -File ./combine-code.ps1
  pwsh -NoProfile -ExecutionPolicy Bypass -File ./combine-code.ps1 -Output CODEBASE.md
  pwsh -NoProfile -ExecutionPolicy Bypass -Command "& { <paste this script> }"

Notes:
- Excludes typical build/log/temp directories and non-text file types.
- Includes common source code, Markdown, and JSON files.
- Adds a table-of-contents and per-file fenced code blocks with language hints.
#>

param(
  [string]$Root = (Resolve-Path .).Path,
  [string]$Output = "ALL_CODE.md"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Info([string]$msg) { Write-Host "[info] $msg" }

# Normalize root and output
$Root = (Resolve-Path $Root).Path
$Output = if ([System.IO.Path]::IsPathRooted($Output)) { $Output } else { Join-Path $Root $Output }

# Ensure output is excluded from the scan (if it already exists)
$outputRel = try { [IO.Path]::GetRelativePath($Root, $Output) } catch { '' }

# Extensions to include (code + markdown + json)
$includeExt = @(
  '.ts','.tsx','.js','.jsx','.mjs','.cjs',
  '.py','.sql','.prisma',
  '.css','.scss','.sass','.html','.htm',
  '.sh','.bash','.ps1','.psm1','.psd1',
  '.go','.rs',
  '.md','.markdown','.mdx',
  '.json'
)

# Directories to exclude (typical build/log/temp/binary caches)
$excludeDirs = @(
  '.git','node_modules','.next','dist','build','out','coverage',
  'logs','log','.turbo','.cache','tmp','temp','reports',
  '__pycache__','.pytest_cache','.mypy_cache','.venv','venv',
  '.idea','.gradle','.parcel-cache','.svelte-kit','.husky',
  '.ds_store','.svn','.hg','archive'
)

# Files to exclude (lockfiles, maps, minified, snapshots, binaries, large assets, and our output)
$excludeNamePatterns = @(
  '*.log','*.jsonl','*.map','*.min.*','*.snap','*.lock',
  'pnpm-lock.yaml','package-lock.json','yarn.lock',
  '*.png','*.jpg','*.jpeg','*.gif','*.svg','*.ico','*.pdf',
  '*.zip','*.gz','*.tar','*.tgz','*.7z',
  '*.exe','*.dll','*.bin','*.dylib','*.so','*.class','*.jar','*.pyc',
  '*.ttf','*.otf','*.woff','*.woff2'
)

if ($outputRel -and $outputRel -ne '.') { $excludeNamePatterns += [IO.Path]::GetFileName($Output) }

# Build an exclude regex for directories
$escaped = $excludeDirs | ForEach-Object { [Regex]::Escape($_) } | Where-Object { $_ -and $_.Trim() -ne '' }
$excludeDirRegex = if ($escaped.Count -gt 0) {
  '(?i)(^|[\\/])(' + ($escaped -join '|') + ')([\\/]|$)'
} else {
  $null
}

# Simple ext -> fenced language mapping
$langMap = @{
  '.ts'='ts'; '.tsx'='tsx'; '.js'='js'; '.jsx'='jsx'; '.mjs'='js'; '.cjs'='js';
  '.py'='python'; '.sql'='sql'; '.prisma'='prisma';
  '.css'='css'; '.scss'='scss'; '.sass'='sass';
  '.html'='html'; '.htm'='html';
  '.sh'='bash'; '.bash'='bash'; '.ps1'='powershell'; '.psm1'='powershell'; '.psd1'='powershell';
  '.go'='go'; '.rs'='rust';
  '.md'='md'; '.markdown'='md'; '.mdx'='mdx';
  '.json'='json'
}

function Get-Fence([string]$text) {
  if ($text -notmatch '```') { return '```' }
  elseif ($text -notmatch '````') { return '````' }
  else { return '~~~~' }
}

function Is-ExcludedFileName([string]$name) {
  foreach ($pat in $excludeNamePatterns) {
    if ([System.Management.Automation.WildcardPattern]::new($pat, 'IgnoreCase').IsMatch($name)) { return $true }
  }
  return $false
}

Write-Info "Scanning: $Root"

# Gather files
$files = Get-ChildItem -Path $Root -File -Recurse -ErrorAction SilentlyContinue |
  Where-Object {
    $rel = [IO.Path]::GetRelativePath($Root, $_.FullName)
    $ext = $_.Extension.ToLowerInvariant()
    # Exclude directories
    if ($excludeDirRegex -and ($rel -match $excludeDirRegex)) { return $false }
    # Include by extension or Dockerfile
    $isDocker = ($_.Name -match '^Dockerfile(\..+)?$')
    if (-not $isDocker -and -not ($includeExt -contains $ext)) { return $false }
    # Exclude by name patterns
    if (Is-ExcludedFileName $_.Name) { return $false }
    # Size guard (skip huge files > 5MB)
    if ($_.Length -gt 5MB) { return $false }
    return $true
  } |
  Sort-Object FullName

if (-not $files -or $files.Count -eq 0) {
  Write-Warning "No files found to include. Check filters."
  exit 0
}

Write-Info ("Including {0} files" -f $files.Count)

# Build header and index
$lines = New-Object System.Collections.Generic.List[string]
$lines.Add("# Combined Code Bundle")
$lines.Add("")
$lines.Add(("Generated: {0:yyyy-MM-dd HH:mm:ss K}" -f [DateTimeOffset]::Now))
$lines.Add(("Root: {0}" -f $Root))
$lines.Add(("Files: {0}" -f $files.Count))
$lines.Add("")
$lines.Add("## Index")
foreach ($f in $files) {
  $rel = [IO.Path]::GetRelativePath($Root, $f.FullName)
  $lines.Add('- `' + $rel.Replace('`','``') + '`')
}
$lines.Add("")

# Append each file content with fenced code blocks
foreach ($f in $files) {
  $rel = [IO.Path]::GetRelativePath($Root, $f.FullName)
  $ext = $f.Extension.ToLowerInvariant()
  $lang = if ($f.Name -match '^Dockerfile(\..+)?$') { 'dockerfile' } else { $langMap[$ext] }
  if (-not $lang) { $lang = 'text' }
  Write-Info "Bundling: $rel"

  $content = Get-Content -LiteralPath $f.FullName -Raw -Encoding UTF8
  $fence = Get-Fence $content

  $lines.Add("\n---\n")
  $lines.Add("### " + $rel)
  $lines.Add("")
  $lines.Add($fence + $lang)
  $lines.Add($content)
  $lines.Add($fence)
}

# Write output (UTF-8)
$null = New-Item -ItemType Directory -Path ([IO.Path]::GetDirectoryName($Output)) -Force -ErrorAction SilentlyContinue
$lines -join "`n" | Set-Content -Path $Output -Encoding utf8
Write-Info "Wrote: $Output"
```

## package.json

```json
{
  "name": "atticus",
  "version": "0.7.4",
  "private": true,
  "description": "Next.js frontend for the Atticus RAG workspace.",
  "scripts": {
    "dev": "next dev -p 3000",
    "build": "next build",
    "start": "next start -p 3000",
    "lint": "next lint",
    "format": "prettier --write .",
    "format:check": "prettier --check .",
    "typecheck": "tsc --noEmit",
    "audit:ts": "knip --strict",
    "audit:icons": "node scripts/icon-audit.mjs",
    "audit:routes": "node scripts/route-audit.mjs",
    "audit:py": "python scripts/audit_unused.py --json",
    "prisma:generate": "prisma generate",
    "db:migrate": "prisma migrate deploy",
    "db:seed": "ts-node --esm prisma/seed.ts",
    "test:unit": "vitest run",
    "test:unit:watch": "vitest",
    "test:e2e": "playwright test"
  },
  "dependencies": {
    "@auth/prisma-adapter": "^2.10.0",
    "@prisma/client": "^5.18.0",
    "clsx": "^2.1.1",
    "lucide-react": "^0.452.0",
    "next": "^14.2.33",
    "next-auth": "^4.24.7",
    "nodemailer": "^6.9.14",
    "react": "18.2.0",
    "react-dom": "18.2.0",
    "zod": "^4.1.11"
  },
  "devDependencies": {
    "@playwright/test": "^1.45.2",
    "@types/node": "20.14.9",
    "@types/nodemailer": "^7.0.1",
    "@types/react": "18.3.5",
    "@types/react-dom": "18.3.0",
    "autoprefixer": "10.4.20",
    "eslint": "8.57.0",
    "eslint-config-next": "14.2.5",
    "eslint-config-prettier": "^9.1.0",
    "eslint-plugin-tailwindcss": "^3.13.0",
    "knip": "^5.64.1",
    "postcss": "8.4.40",
    "prettier": "^3.3.3",
    "prettier-plugin-tailwindcss": "^0.5.14",
    "prisma": "^5.18.0",
    "tailwindcss": "3.4.10",
    "ts-node": "^10.9.2",
    "typescript": "5.4.5",
    "vitest": "^3.2.4"
  }
}
```

## pyproject.toml

```toml
[project]
name = "atticus"
dynamic = ["version"]

description = "Atticus Retrieval-Augmented Generation service"
readme = "README.md"
authors = [{ name = "Atticus Ops", email = "ops@example.com" }]
requires-python = ">=3.12"
dependencies = []

[project.optional-dependencies]
dev = [
  "pip-tools",
  "ruff>=0.5",
  "mypy>=1.10",
  "pytest>=8",
  "pytest-cov>=5",
  "pytest-sugar>=0.9.7",
  "pytest-xdist>=3.5",
  "pydantic>=2.7",
  "types-requests",
  "types-PyYAML",
  "vulture>=2.11",
  # Include psycopg wheels so `pip install -e .[dev]` matches Prisma migrations locally
  "psycopg[binary]>=3.2",
  "pre-commit>=3.7"
]

[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[tool.setuptools]
packages = ["atticus", "api", "ingest", "retriever", "eval"]

[tool.setuptools.dynamic]
version = { file = "VERSION" }

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP", "ASYNC", "RUF", "PL"]
ignore = [
  "E501",
  "E402",
  "PLR0912",
  "PLR0913",
  "PLR0915",
  "PLR2004",
  "B023",
  "E731",
  "UP035",
  "RUF012",
  "RUF046",
  "RUF100",
]

[tool.ruff.lint.per-file-ignores]
"tests/*" = ["PLR2004", "PLC0415", "PLR0913", "I001"]
"retriever/generator.py" = ["RUF001"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
line-ending = "lf"

[tool.mypy]
python_version = "3.12"
strict = true
packages = ["atticus", "api", "ingest", "retriever", "eval"]
plugins = ["pydantic.mypy"]
ignore_missing_imports = true
warn_unused_configs = true
warn_unused_ignores = true
warn_redundant_casts = true
warn_return_any = true
exclude = "^(scripts|tests|EXAMPLES_ONLY)/"

[[tool.mypy.overrides]]
module = [
  "atticus.vector_db",
  "api.routes.admin",
  "api.main",
  "eval.runner",
]
ignore_errors = true

[tool.pytest.ini_options]
minversion = "7.0"
addopts = "-ra"
testpaths = ["tests", "eval/harness"]
markers = ["eval: evaluation harness"]
filterwarnings = [
  # Safe to ignore: upstream SWIG/PyMuPDF deprecation noise
  "ignore:.*SwigPyPacked.*:DeprecationWarning",
  "ignore:.*SwigPyObject.*:DeprecationWarning",
  "ignore:.*swigvarlink.*:DeprecationWarning",
]

[tool.coverage.run]
source = ["atticus", "api", "retriever"]
omit = [
  # Temporarily exempted modules pending integration tests
  "api/routes/ask.py",
  "atticus/config.py",
  "atticus/logging.py",
  "atticus/embeddings.py",
  "atticus/vector_db.py",
  "atticus/metrics.py",
  "atticus/tokenization.py",
  "atticus/notify/mailer.py",
  "retriever/generator.py",
  "retriever/vector_store.py",
  "retriever/service.py",
  "api/routes/admin.py",
  "api/routes/eval.py",
  "api/routes/ingest.py",
  "api/routes/health.py",
  "api/dependencies.py",
  "api/middleware.py",
  "api/utils.py",
]

[tool.coverage.report]
fail_under = 90
show_missing = true
```

## requirements.in

```
# Core runtime
fastapi
uvicorn
uvloop; sys_platform != 'win32'
httptools
websockets
watchfiles
pydantic
pydantic-settings
httpx
python-dotenv
# Postgres driver – binary wheels keep setup simple across macOS/Windows until we switch fully to Prisma
psycopg[binary]
pgvector
openai
numpy
scikit-learn
rapidfuzz
tiktoken

# Parsing / ingestion
pymupdf
pdfminer.six
pytesseract
Pillow
python-docx
openpyxl
beautifulsoup4
pandas
camelot-py
tabula-py

# Utilities
tenacity
structlog
pyyaml

# Testing
pytest
pytest-cov
pytest-sugar
pytest-xdist

# Tooling
ruff
mypy
types-PyYAML
pip-tools
vulture
```

## requirements.txt

```
#
# This file is autogenerated by pip-compile with Python 3.12
# by the following command:
#
#    pip-compile requirements.in
#
annotated-types==0.7.0
    # via pydantic
anyio==4.11.0
    # via
    #   httpx
    #   openai
    #   starlette
    #   watchfiles
beautifulsoup4==4.14.2
    # via -r requirements.in
build==1.3.0
    # via pip-tools
camelot-py==1.0.9
    # via -r requirements.in
certifi==2025.10.5
    # via
    #   httpcore
    #   httpx
    #   requests
cffi==2.0.0
    # via cryptography
chardet==5.2.0
    # via camelot-py
charset-normalizer==3.4.3
    # via
    #   pdfminer-six
    #   requests
click==8.3.0
    # via
    #   camelot-py
    #   pip-tools
    #   uvicorn
colorama==0.4.6
    # via
    #   build
    #   click
    #   pytest
    #   tqdm
coverage[toml]==7.10.7
    # via pytest-cov
cryptography==46.0.2
    # via pdfminer-six
distro==1.9.0
    # via
    #   openai
    #   tabula-py
et-xmlfile==2.0.0
    # via openpyxl
execnet==2.1.1
    # via pytest-xdist
fastapi==0.118.0
    # via -r requirements.in
h11==0.16.0
    # via
    #   httpcore
    #   uvicorn
httpcore==1.0.9
    # via httpx
httptools==0.6.4
    # via -r requirements.in
httpx==0.28.1
    # via
    #   -r requirements.in
    #   openai
idna==3.10
    # via
    #   anyio
    #   httpx
    #   requests
iniconfig==2.1.0
    # via pytest
jiter==0.11.0
    # via openai
joblib==1.5.2
    # via scikit-learn
lxml==6.0.2
    # via python-docx
mypy==1.18.2
    # via -r requirements.in
mypy-extensions==1.1.0
    # via mypy
numpy==2.2.6
    # via
    #   -r requirements.in
    #   camelot-py
    #   opencv-python-headless
    #   pandas
    #   pgvector
    #   scikit-learn
    #   scipy
    #   tabula-py
openai==2.2.0
    # via -r requirements.in
opencv-python-headless==4.12.0.88
    # via camelot-py
openpyxl==3.1.5
    # via
    #   -r requirements.in
    #   camelot-py
packaging==25.0
    # via
    #   build
    #   pytesseract
    #   pytest
pandas==2.3.3
    # via
    #   -r requirements.in
    #   camelot-py
    #   tabula-py
pathspec==0.12.1
    # via mypy
pdfminer-six==20250506
    # via
    #   -r requirements.in
    #   camelot-py
pgvector==0.4.1
    # via -r requirements.in
pillow==11.3.0
    # via
    #   -r requirements.in
    #   camelot-py
    #   pytesseract
pip-tools==7.5.1
    # via -r requirements.in
pluggy==1.6.0
    # via
    #   pytest
    #   pytest-cov
psycopg[binary]==3.2.10
    # via -r requirements.in
psycopg-binary==3.2.10
    # via psycopg
pycparser==2.23
    # via cffi
pydantic==2.12.0
    # via
    #   -r requirements.in
    #   fastapi
    #   openai
    #   pydantic-settings
pydantic-core==2.41.1
    # via pydantic
pydantic-settings==2.11.0
    # via -r requirements.in
pygments==2.19.2
    # via pytest
pymupdf==1.26.4
    # via -r requirements.in
pypdf==5.9.0
    # via camelot-py
pypdfium2==4.30.0
    # via camelot-py
pyproject-hooks==1.2.0
    # via
    #   build
    #   pip-tools
pytesseract==0.3.13
    # via -r requirements.in
pytest==8.4.2
    # via
    #   -r requirements.in
    #   pytest-cov
    #   pytest-sugar
    #   pytest-xdist
pytest-cov==7.0.0
    # via -r requirements.in
pytest-sugar==1.1.1
    # via -r requirements.in
pytest-xdist==3.8.0
    # via -r requirements.in
python-dateutil==2.9.0.post0
    # via pandas
python-docx==1.2.0
    # via -r requirements.in
python-dotenv==1.1.1
    # via
    #   -r requirements.in
    #   pydantic-settings
pytz==2025.2
    # via pandas
pyyaml==6.0.3
    # via -r requirements.in
rapidfuzz==3.14.1
    # via -r requirements.in
regex==2025.9.18
    # via tiktoken
requests==2.32.5
    # via tiktoken
ruff==0.14.0
    # via -r requirements.in
scikit-learn==1.7.2
    # via -r requirements.in
scipy==1.16.2
    # via scikit-learn
six==1.17.0
    # via python-dateutil
sniffio==1.3.1
    # via
    #   anyio
    #   openai
soupsieve==2.8
    # via beautifulsoup4
starlette==0.48.0
    # via fastapi
structlog==25.4.0
    # via -r requirements.in
tabula-py==2.10.0
    # via -r requirements.in
tabulate==0.9.0
    # via camelot-py
tenacity==9.1.2
    # via -r requirements.in
termcolor==3.1.0
    # via pytest-sugar
threadpoolctl==3.6.0
    # via scikit-learn
tiktoken==0.12.0
    # via -r requirements.in
tqdm==4.67.1
    # via openai
types-pyyaml==6.0.12.20250915
    # via -r requirements.in
typing-extensions==4.15.0
    # via
    #   anyio
    #   beautifulsoup4
    #   fastapi
    #   mypy
    #   openai
    #   psycopg
    #   pydantic
    #   pydantic-core
    #   python-docx
    #   starlette
    #   typing-inspection
typing-inspection==0.4.2
    # via
    #   pydantic
    #   pydantic-settings
tzdata==2025.2
    # via
    #   pandas
    #   psycopg
urllib3==2.5.0
    # via requests
uvicorn==0.37.0
    # via -r requirements.in
vulture==2.14
    # via -r requirements.in
watchfiles==1.1.0
    # via -r requirements.in
websockets==15.0.1
    # via -r requirements.in
wheel==0.45.1
    # via pip-tools

# The following packages are considered to be unsafe in a requirements file:
# pip
# setuptools
```

## scripts/audit_unused.py

```python
#!/usr/bin/env python3
"""Audit script for unused Python modules and dead code.

Runs vulture (if installed) against default project paths and prints a JSON
summary. The script degrades gracefully when optional tools are missing.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULT_PATHS: list[str] = [
    "atticus",
    "api",
    "ingest",
    "retriever",
    "eval",
    "scripts",
    "tests",
]


def run_vulture(paths: list[str], min_confidence: int) -> dict[str, object]:
    executable = shutil.which("vulture")
    if executable is None:
        return {
            "tool": "vulture",
            "error": "vulture not installed. Install with `pip install vulture` or add to dev dependencies.",
        }

    cmd: list[str] = [executable, *paths, "--min-confidence", str(min_confidence), "--sort-by-size"]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    return {
        "tool": "vulture",
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Audit unused Python code via vulture")
    parser.add_argument("paths", nargs="*", default=DEFAULT_PATHS, help="Paths to inspect")
    parser.add_argument(
        "--min-confidence", type=int, default=80, help="Minimum confidence threshold for vulture"
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON output")
    args = parser.parse_args(argv)

    resolved_paths: list[str] = []
    for path in args.paths:
        candidate = Path(path)
        if candidate.exists():
            resolved_paths.append(str(candidate))
    if not resolved_paths:
        resolved_paths = DEFAULT_PATHS

    report = {"vulture": run_vulture(resolved_paths, args.min_confidence)}

    if args.json:
        json.dump(report, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        sys.stdout.write(json.dumps(report, indent=2))
        sys.stdout.write("\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
```

## scripts/chunk_ced.py

```python
#!/usr/bin/env python3
"""Chunk CED PDF documents into JSONL artifacts."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from statistics import median

import fitz  # type: ignore[import-untyped]

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from atticus.config import load_settings  # noqa: E402
from atticus.tokenization import decode, encode, split_tokens  # noqa: E402
from atticus.utils import sha256_file, sha256_text  # noqa: E402

try:  # pragma: no cover - optional dependency
    import camelot  # type: ignore[import-untyped]
except Exception:  # pragma: no cover
    camelot = None

try:  # pragma: no cover - optional dependency
    import tabula  # type: ignore[import-untyped]
except Exception:  # pragma: no cover
    tabula = None

STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "that",
    "from",
    "this",
    "will",
    "your",
    "have",
    "into",
    "when",
    "where",
    "such",
    "each",
    "over",
    "there",
    "should",
    "their",
    "which",
    "these",
    "between",
}

HEADING_WORD_LIMIT = 12
TABLE_EMPTY_RATIO = 0.2
GARBLE_THRESHOLD = 0.05
FONT_SIZE_PADDING = 2.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Chunk a CED PDF into JSONL outputs")
    parser.add_argument("--input", type=Path, required=True, help="Path to the source PDF")
    parser.add_argument("--output", type=Path, required=True, help="JSONL file for text chunks")
    parser.add_argument("--tables", type=Path, required=True, help="JSONL file for table chunks")
    parser.add_argument(
        "--doc-index",
        type=Path,
        required=True,
        help="Path to write document-level index metadata",
    )
    parser.add_argument("--target-tokens", type=int)
    parser.add_argument("--min-tokens", type=int)
    parser.add_argument("--overlap", type=int)
    parser.add_argument("--config", type=Path, help="Alternate config.yaml path")
    return parser.parse_args()


@dataclass(slots=True)
class Section:
    heading: str | None
    text: str
    pages: set[int]
    breadcrumbs: list[str]


@dataclass(slots=True)
class Chunk:
    text: str
    pages: set[int]
    headings: set[str]
    breadcrumbs: list[str]
    token_count: int
    is_table: bool = False
    table_headers: list[str] | None = None


def _sanitize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _extract_models(source: Path) -> list[str]:
    stem = source.stem
    match = re.search(r"CED[-_]?(\d+)", stem, flags=re.IGNORECASE)
    prefix = stem
    if match:
        prefix = stem[: match.start()].rstrip("-_ ")
    if "_" in prefix:
        prefix = prefix.split("_", 1)[1]
    models_part = re.split(r"-CED[-_]?\d+", prefix, flags=re.IGNORECASE)[0]
    raw_models = [item for item in re.split(r"[-_]", models_part) if item]
    return raw_models


def _ced_id(source: Path) -> tuple[str, str]:
    match = re.search(r"CED[-_]?(\d+)", source.stem, flags=re.IGNORECASE)
    if not match:
        return ("ced-unknown", "0")
    value = match.group(1)
    return (f"ced-{value}", value)


def _compute_font_baseline(document: fitz.Document) -> float:
    sizes: list[float] = []
    for page in document:
        content = page.get_text("dict")
        for block in content.get("blocks", []):
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    size = span.get("size")
                    if size:
                        sizes.append(float(size))
    if not sizes:
        return 11.0
    return median(sizes)


def extract_sections(document: fitz.Document, heading_threshold: float) -> list[Section]:
    sections: list[Section] = []
    buffer: list[str] = []
    pages: set[int] = set()
    current_heading: str | None = None

    def flush() -> None:
        nonlocal buffer, pages
        if not buffer:
            return
        sections.append(
            Section(
                heading=current_heading,
                text="\n".join(buffer).strip(),
                pages=pages.copy() or {1},
                breadcrumbs=[
                    breadcrumb for breadcrumb in ([current_heading] if current_heading else [])
                ],
            )
        )
        buffer.clear()
        pages.clear()

    for index, page in enumerate(document, start=1):
        page_dict = page.get_text("dict")
        for block in page_dict.get("blocks", []):
            for line in block.get("lines", []):
                spans = line.get("spans", [])
                text = _sanitize("".join(span.get("text", "") for span in spans))
                if not text:
                    continue
                max_size = max(float(span.get("size", 0.0)) for span in spans)
                if max_size >= heading_threshold and len(text.split()) <= HEADING_WORD_LIMIT:
                    flush()
                    current_heading = text
                    continue
                buffer.append(text)
                pages.add(index)

    flush()
    return sections


def extract_tables(path: Path) -> list[Chunk]:  # noqa: PLR0912
    tables: list[Chunk] = []
    if camelot is not None:  # pragma: no cover - requires camelot deps
        try:
            camelot_tables = camelot.read_pdf(str(path), pages="all")
        except Exception:
            camelot_tables = []
        for index, table in enumerate(camelot_tables, start=1):
            try:
                dataframe = table.df  # type: ignore[attr-defined]
            except Exception:
                continue
            if dataframe.empty:
                continue
            cleaned = dataframe.fillna("")
            total_cells = cleaned.size
            empty_cells = sum(1 for value in cleaned.to_numpy().flatten() if not str(value).strip())
            if total_cells and (empty_cells / total_cells) > TABLE_EMPTY_RATIO:
                continue
            header = [str(item).strip() for item in cleaned.iloc[0].tolist()]
            body = cleaned.iloc[1:]
            rows = [
                " | ".join(str(cell).strip() for cell in row.tolist()) for _, row in body.iterrows()
            ]
            text = "\n".join(rows).strip()
            if not text:
                continue
            table_breadcrumbs = [f"Table {index}"]
            tables.append(
                Chunk(
                    text=text,
                    pages={int(getattr(table, "page", 1))},
                    headings={f"Table {index}"},
                    breadcrumbs=table_breadcrumbs,
                    token_count=len(encode(text)),
                    is_table=True,
                    table_headers=header,
                )
            )
        if tables:
            return tables
    if tabula is not None:  # pragma: no cover - requires java
        try:
            dataframes = tabula.read_pdf(str(path), pages="all", multiple_tables=True)
        except Exception:
            dataframes = []
        for index, dataframe in enumerate(dataframes, start=1):
            if dataframe is None or dataframe.empty:
                continue
            cleaned = dataframe.fillna("")
            total_cells = cleaned.size
            empty_cells = sum(1 for value in cleaned.to_numpy().flatten() if not str(value).strip())
            if total_cells and (empty_cells / total_cells) > TABLE_EMPTY_RATIO:
                continue
            header = [str(col).strip() for col in cleaned.columns]
            rows = [" | ".join(str(cell).strip() for cell in row) for row in cleaned.to_numpy()]
            text = "\n".join(rows).strip()
            if not text:
                continue
            table_breadcrumbs = [f"Table {index}"]
            tables.append(
                Chunk(
                    text=text,
                    pages={1},
                    headings={f"Table {index}"},
                    breadcrumbs=table_breadcrumbs,
                    token_count=len(encode(text)),
                    is_table=True,
                    table_headers=header,
                )
            )
    return tables


def merge_small_chunks(chunks: list[Chunk], min_tokens: int) -> list[Chunk]:
    if not chunks:
        return chunks
    merged: list[Chunk] = []
    for chunk in chunks:
        if merged and chunk.token_count < min_tokens and not chunk.is_table:
            target = merged[-1]
            target.text = f"{target.text}\n{chunk.text}".strip()
            target.token_count += chunk.token_count
            target.pages.update(chunk.pages)
            target.headings.update(chunk.headings)
            target.breadcrumbs = list(dict.fromkeys(target.breadcrumbs + chunk.breadcrumbs))
        else:
            merged.append(chunk)
    return merged


def chunk_sections(
    sections: list[Section],
    target_tokens: int,
    min_tokens: int,
    overlap: int,
    base_breadcrumbs: list[str],
) -> list[Chunk]:
    all_chunks: list[Chunk] = []
    for section in sections:
        tokens = encode(section.text)
        if not tokens:
            continue
        splits = list(split_tokens(tokens, target_tokens, overlap))
        section_chunks: list[Chunk] = []
        for start, end in splits:
            piece = tokens[start:end]
            text = decode(piece).strip()
            if not text:
                continue
            section_chunks.append(
                Chunk(
                    text=text,
                    pages=section.pages.copy() or {1},
                    headings={heading for heading in [section.heading] if heading},
                    breadcrumbs=list(
                        dict.fromkeys(
                            base_breadcrumbs + (section.breadcrumbs if section.breadcrumbs else [])
                        )
                    ),
                    token_count=len(piece),
                )
            )
        section_chunks = merge_small_chunks(section_chunks, min_tokens)
        all_chunks.extend(section_chunks)
    return all_chunks


def garble_ratio(text: str) -> float:
    if not text:
        return 0.0
    garbled = sum(1 for char in text if char == "\ufffd")
    return garbled / max(1, len(text))


def summarize(text: str) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return sentences[0][:240] if sentences else text[:240]


def extract_keywords(text: str, top_n: int = 5) -> list[str]:
    words = [re.sub(r"[^a-z0-9]", "", token.lower()) for token in text.split()]
    words = [word for word in words if word and word not in STOPWORDS]
    counts = Counter(words)
    return [word for word, _ in counts.most_common(top_n)]


def write_jsonl(path: Path, entries: Iterable[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for entry in entries:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def main() -> None:
    args = parse_args()
    if args.config:
        os.environ["CONFIG_PATH"] = str(args.config)

    settings = load_settings()
    source_file = args.input
    if not source_file.exists():
        raise FileNotFoundError(source_file)

    ced_id, version = _ced_id(source_file)
    models = _extract_models(source_file)
    timestamp = datetime.utcnow().isoformat(timespec="seconds") + "Z"

    document = fitz.open(str(source_file))
    font_baseline = _compute_font_baseline(document)
    sections = extract_sections(document, font_baseline + FONT_SIZE_PADDING)
    tables = extract_tables(source_file)
    base_breadcrumbs = [ced_id.upper(), source_file.stem]
    target_tokens = args.target_tokens or settings.chunk_target_tokens or 800
    min_tokens = args.min_tokens or settings.chunk_min_tokens or 400
    if args.overlap is not None:
        overlap = max(0, args.overlap)
    else:
        overlap = settings.chunk_overlap_tokens
    chunks = chunk_sections(sections, target_tokens, min_tokens, overlap, base_breadcrumbs)
    document.close()

    chunk_payloads: list[dict[str, object]] = []
    table_payloads: list[dict[str, object]] = []
    chunk_index = 0
    for chunk in chunks:
        if garble_ratio(chunk.text) > GARBLE_THRESHOLD:
            continue
        chunk_index += 1
        pages = sorted(chunk.pages)
        models_present = [model for model in models if model.lower() in chunk.text.lower()]
        payload = {
            "chunk_id": f"{ced_id}::chunk_{chunk_index:04d}",
            "source_file": str(source_file),
            "doc_type": "ced",
            "ced_id": ced_id,
            "version": version,
            "page_range": pages,
            "section_titles": sorted(chunk.headings),
            "breadcrumbs": chunk.breadcrumbs or base_breadcrumbs,
            "is_table": False,
            "table_headers": [],
            "models": models,
            "models_present": models_present,
            "token_index": chunk_index - 1,
            "token_count": chunk.token_count,
            "embedding_model": settings.embed_model,
            "embedding_model_version": settings.embedding_model_version,
            "ingested_at": timestamp,
            "hash": sha256_text(chunk.text),
            "keywords": extract_keywords(chunk.text),
            "context_summary": summarize(chunk.text),
            "text": chunk.text,
        }
        chunk_payloads.append(payload)

    table_index = 0
    for table in tables:
        if garble_ratio(table.text) > GARBLE_THRESHOLD:
            continue
        table_index += 1
        pages = sorted(table.pages)
        models_present = [model for model in models if model.lower() in table.text.lower()]
        payload = {
            "table_id": f"{ced_id}::table_{table_index:04d}",
            "source_file": str(source_file),
            "doc_type": "ced",
            "ced_id": ced_id,
            "version": version,
            "page_range": pages,
            "section_titles": sorted(table.headings),
            "breadcrumbs": table.breadcrumbs or base_breadcrumbs,
            "is_table": True,
            "table_headers": table.table_headers or [],
            "models": models,
            "models_present": models_present,
            "token_index": chunk_index + table_index - 1,
            "token_count": table.token_count,
            "embedding_model": settings.embed_model,
            "embedding_model_version": settings.embedding_model_version,
            "ingested_at": timestamp,
            "hash": sha256_text(table.text),
            "keywords": extract_keywords(table.text),
            "context_summary": summarize(table.text),
            "text": table.text,
        }
        table_payloads.append(payload)

    write_jsonl(args.output, chunk_payloads)
    write_jsonl(args.tables, table_payloads)

    doc_index = {
        "ced_id": ced_id,
        "version": version,
        "source_file": str(source_file),
        "models": models,
        "chunk_count": len(chunk_payloads),
        "table_count": len(table_payloads),
        "generated_at": timestamp,
        "embedding_model": settings.embed_model,
        "embedding_model_version": settings.embedding_model_version,
        "document_hash": sha256_file(source_file),
    }
    args.doc_index.parent.mkdir(parents=True, exist_ok=True)
    args.doc_index.write_text(json.dumps(doc_index, indent=2), encoding="utf-8")

    print(
        json.dumps(
            {
                "chunks": len(chunk_payloads),
                "tables": len(table_payloads),
                "doc_index": str(args.doc_index),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
```

## scripts/db_verify.py

```python
"""Helper to invoke the pgvector verification SQL in a cross-platform way."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile


def _load_env_from_file(env_path: Path) -> None:
    """Populate os.environ with values from `.env` if they are not already set."""
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        key, sep, value = line.partition("=")
        if not sep:
            continue
        key = key.strip()
        if not key or key in os.environ:
            continue
        cleaned = value.strip()
        if (cleaned.startswith('"') and cleaned.endswith('"')) or (cleaned.startswith("'") and cleaned.endswith("'")):
            cleaned = cleaned[1:-1]
        os.environ[key] = cleaned


def main() -> int:
    _load_env_from_file(Path(".env"))

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL is not set. Export it before running db.verify.", file=sys.stderr)
        return 1

    sql_path = Path("scripts/verify_pgvector.sql")
    if not sql_path.exists():
        print("scripts/verify_pgvector.sql not found.", file=sys.stderr)
        return 1

    dimension = os.environ.get("PGVECTOR_DIMENSION", "3072")
    lists = os.environ.get("PGVECTOR_LISTS", "100")
    sql_template = sql_path.read_text(encoding="utf-8")
    sql_rendered = (
        sql_template.replace(":expected_pgvector_dimension", dimension).replace(":expected_pgvector_lists", lists)
    )

    with NamedTemporaryFile("w", encoding="utf-8", suffix=".sql", delete=False) as tmp_file:
        tmp_file.write(sql_rendered)
        tmp_path = Path(tmp_file.name)

    extra_cleanup: list[list[str]] = [["rm", "-f", str(tmp_path)]]

    psql_path = shutil.which("psql")
    docker_path = shutil.which("docker")
    docker_compose_path = shutil.which("docker-compose")

    compose_base: list[str] | None = None

    if psql_path:
        command_prefix: list[str] = [psql_path]
        sql_arg = str(tmp_path)
    else:
        if docker_path:
            compose_base = [docker_path, "compose"]
        elif docker_compose_path:
            compose_base = [docker_compose_path]
        else:
            print(
                "psql is required but not found on PATH, and docker compose is unavailable for fallback execution.",
                file=sys.stderr,
            )
            return 1

        command_prefix = compose_base + ["exec", "-T", "postgres", "psql"]
        remote_path = "/tmp/verify_pgvector.sql"
        copy_cmd = compose_base + ["cp", str(tmp_path), f"postgres:{remote_path}"]
        subprocess.run(copy_cmd, check=True)
        sql_arg = remote_path
        extra_cleanup.append(compose_base + ["exec", "-T", "postgres", "rm", "-f", remote_path])

    cmd: list[str] = command_prefix + [
        "--dbname",
        database_url,
        "-v",
        f"expected_pgvector_dimension={dimension}",
        "-v",
        f"expected_pgvector_lists={lists}",
        "-f",
        sql_arg,
    ]

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as exc:
        return exc.returncode
    finally:
        for cleanup_cmd in extra_cleanup:
            try:
                if cleanup_cmd[0] == "rm":
                    Path(cleanup_cmd[-1]).unlink(missing_ok=True)
                else:
                    subprocess.run(cleanup_cmd, check=False)
            except Exception:
                pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
```

## scripts/debug_env.py

```python
#!/usr/bin/env python3
"""Inspect Atticus environment configuration without leaking secrets."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from atticus.config import environment_diagnostics, reset_settings_cache  # noqa: E402


def main() -> int:
    diagnostics = environment_diagnostics()
    diagnostics["repo_root"] = str(ROOT)
    print(json.dumps(diagnostics, indent=2, sort_keys=True))
    reset_settings_cache()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

## scripts/e2e_smoke.py

```python
"""E2E smoke checks for Atticus API and UI make targets."""

from __future__ import annotations

import contextlib
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import requests

HOST = os.environ.get("ATTICUS_E2E_HOST", "127.0.0.1")
API_PORT = int(os.environ.get("ATTICUS_API_PORT", "8000"))
UI_PORT = int(os.environ.get("ATTICUS_UI_PORT", "8081"))
ROOT = Path(__file__).resolve().parents[1]
WEB_DIR = ROOT / "web"


class ManagedProcess:
    """Launch a long-running command and surface logs if checks fail."""

    def __init__(self, name: str, args: list[str], cwd: Path) -> None:
        self.name = name
        self.args = args
        self.cwd = cwd
        self.proc: subprocess.Popen | None = None
        self.stdout: str = ""
        self.stderr: str = ""
        self._should_dump = False

    def __enter__(self) -> ManagedProcess:
        self.proc = subprocess.Popen(
            self.args,
            cwd=self.cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        self._should_dump = exc_type is not None
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
        if self.proc:
            try:
                out, err = self.proc.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                out, err = self.proc.communicate()
            self.stdout = out or ""
            self.stderr = err or ""
            if self._should_dump:
                if self.stdout.strip():
                    print(f"[{self.name} stdout]\n{self.stdout}")
                if self.stderr.strip():
                    print(f"[{self.name} stderr]\n{self.stderr}", file=sys.stderr)
        return False


def wait_for_port(host: str, port: int, timeout: float = 20.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            sock.settimeout(1.0)
            if sock.connect_ex((host, port)) == 0:
                return
        time.sleep(0.25)
    raise RuntimeError(f"Timed out waiting for {host}:{port}")


def request_with_retry(url: str, *, attempts: int = 5, delay: float = 0.5) -> requests.Response:
    last_error: Exception | None = None
    for _ in range(attempts):
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            return response
        except requests.RequestException as exc:
            last_error = exc
            time.sleep(delay)
    raise RuntimeError(f"Failed to GET {url}") from last_error


def check_api(host: str, port: int) -> None:
    base = f"http://{host}:{port}"
    health = request_with_retry(f"{base}/health")
    payload = health.json()
    if payload.get("status") != "ok":
        raise RuntimeError("API health check did not return status 'ok'")

    root_page = request_with_retry(f"{base}/")
    lower_html = root_page.text.lower()
    if "<html" not in lower_html or "atticus" not in lower_html:
        raise RuntimeError("API root did not render an Atticus UI shell")
    if "/static/" not in lower_html:
        raise RuntimeError("API root is missing static asset references")

    static_asset = request_with_retry(f"{base}/static/js/script.js")
    if not static_asset.text.strip():
        raise RuntimeError("API static assets are empty or missing")


def check_ui(host: str, port: int) -> None:
    base = f"http://{host}:{port}"
    ui_page = request_with_retry(f"{base}/templates/index.html")
    lower_html = ui_page.text.lower()
    if "<html" not in lower_html or "atticus" not in lower_html:
        raise RuntimeError("Standalone UI did not include Atticus branding")
    if "/static/" not in lower_html:
        raise RuntimeError("Standalone UI page is missing static asset references")

    ui_script = request_with_retry(f"{base}/static/js/script.js")
    if not ui_script.text.strip():
        raise RuntimeError("Standalone UI cannot serve static JavaScript")


def main() -> None:
    if not WEB_DIR.exists():
        raise RuntimeError(f"Expected UI directory at {WEB_DIR}")

    api_cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "api.main:app",
        "--port",
        str(API_PORT),
    ]
    ui_cmd = [
        sys.executable,
        "-m",
        "http.server",
        str(UI_PORT),
        "--directory",
        str(WEB_DIR),
    ]

    with ManagedProcess("api", api_cmd, ROOT):
        wait_for_port(HOST, API_PORT)
        check_api(HOST, API_PORT)
        print(f"API smoke passed on {HOST}:{API_PORT}")

        with ManagedProcess("ui", ui_cmd, ROOT):
            wait_for_port(HOST, UI_PORT)
            check_ui(HOST, UI_PORT)
            print(f"UI static smoke passed on {HOST}:{UI_PORT}")

    print("E2E API/UI checks completed.")


if __name__ == "__main__":
    main()
```

## scripts/eval_qa.py

```python
#!/usr/bin/env python3
"""Run simple end-to-end QA evaluation using expected answers.

For each gold example with an `expected_answer`, this script:
- calls the retrieval+generation pipeline (`answer_question`)
- computes token-level F1 between model response and expected
- computes embedding cosine similarity between response and expected

Outputs a CSV and JSON summary alongside the retrieval metrics outputs for the same day.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from collections import Counter
from collections.abc import Iterable
from pathlib import Path

import numpy as np

# Ensure repository root on sys.path for local imports
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from atticus.config import AppSettings, load_settings  # noqa: E402
from atticus.embeddings import EmbeddingClient  # noqa: E402
from eval.runner import _default_output_dir, load_gold_set  # noqa: E402
from retriever.service import answer_question  # noqa: E402


def _tokens(text: str) -> list[str]:
    return [t for t in "".join(c.lower() if c.isalnum() else " " for c in text).split() if t]


def _f1(a: str, b: str) -> float:
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    set_a = ta
    set_b = tb
    ca, cb = Counter(set_a), Counter(set_b)
    common = sum((ca & cb).values())
    if common == 0:
        return 0.0
    precision = common / max(1, sum(cb.values()))
    recall = common / max(1, sum(ca.values()))
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def _cosine(a: Iterable[float], b: Iterable[float]) -> float:
    va = np.array(list(a), dtype=float)
    vb = np.array(list(b), dtype=float)
    na = np.linalg.norm(va)
    nb = np.linalg.norm(vb)
    if na == 0 or nb == 0:
        return 0.0
    return float(va.dot(vb) / (na * nb))


def run_qa_eval(
    settings: AppSettings, gold_path: Path | None = None, output_dir: Path | None = None
) -> dict[str, object]:
    gold_path = gold_path or settings.gold_set_path
    output_dir = output_dir or _default_output_dir(settings)
    examples = [g for g in load_gold_set(gold_path) if g.expected_answer]

    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "qa_metrics.csv"
    json_path = output_dir / "qa_summary.json"

    if not examples:
        payload = {"count": 0, "avg_f1": 0.0, "avg_cosine": 0.0}
        json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return payload

    embed = EmbeddingClient(settings)
    f1_scores: list[float] = []
    cos_scores: list[float] = []
    rows: list[dict[str, object]] = []

    for ex in examples:
        ans = answer_question(ex.question, settings=settings)
        f1 = _f1(ans.response, ex.expected_answer or "")
        v_expected, v_response = embed.embed_texts([ex.expected_answer or "", ans.response])
        cos = _cosine(v_expected, v_response)
        top_doc = ans.citations[0].source_path if ans.citations else None
        f1_scores.append(f1)
        cos_scores.append(cos)
        rows.append(
            {
                "question": ex.question,
                "top_document": top_doc,
                "confidence": ans.confidence,
                "f1": round(f1, 4),
                "cosine": round(cos, 4),
            }
        )

    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=["question", "top_document", "confidence", "f1", "cosine"]
        )
        writer.writeheader()
        writer.writerows(rows)
        writer.writerow(
            {
                "question": "AVERAGE",
                "top_document": "",
                "confidence": round(sum(r.get("confidence", 0.0) for r in rows) / len(rows), 4),
                "f1": round(sum(f1_scores) / len(f1_scores), 4),
                "cosine": round(sum(cos_scores) / len(cos_scores), 4),
            }
        )

    payload = {
        "count": len(rows),
        "avg_f1": round(sum(f1_scores) / len(f1_scores), 4),
        "avg_cosine": round(sum(cos_scores) / len(cos_scores), 4),
        "summary_csv": str(csv_path),
        "summary_json": str(json_path),
    }
    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Run QA eval using expected answers in the gold set")
    p.add_argument("--gold-set", type=Path, help="Optional path to override the default gold set")
    p.add_argument("--output-dir", type=Path, help="Directory for storing QA eval outputs")
    p.add_argument("--config", type=Path, help="Path to an alternate config.yaml file")
    p.add_argument("--json", action="store_true", help="Print results as JSON to stdout")
    return p


def main() -> None:
    args = build_parser().parse_args()
    if args.config:
        os.environ["CONFIG_PATH"] = str(args.config)

    settings = load_settings()
    result = run_qa_eval(settings, gold_path=args.gold_set, output_dir=args.output_dir)
    if args.json or not args.output_dir:
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
```

## scripts/eval_run.py

```python
#!/usr/bin/env python3
"""Run the Atticus evaluation harness from the command line."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from atticus.config import load_settings  # noqa: E402
from eval.runner import run_evaluation  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Execute the retrieval evaluation harness")
    parser.add_argument(
        "--gold-set",
        type=Path,
        help="Optional path to override the default gold set",
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        help="Optional path to override the baseline metrics JSON",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Directory for storing evaluation outputs",
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to an alternate config.yaml file",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print results as JSON to stdout",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.config:
        os.environ["CONFIG_PATH"] = str(args.config)

    settings = load_settings()
    result = run_evaluation(
        settings=settings,
        gold_path=args.gold_set,
        baseline_path=args.baseline,
        output_dir=args.output_dir,
    )

    payload = {
        "metrics": result.metrics,
        "deltas": result.deltas,
        "summary_csv": str(result.summary_csv),
        "summary_json": str(result.summary_json),
        "summary_html": str(result.summary_html),
    }

    if args.json or not args.output_dir:
        print(json.dumps(payload, indent=2))
    else:
        (args.output_dir / "run_summary.json").write_text(
            json.dumps(payload, indent=2), encoding="utf-8"
        )

    threshold = settings.eval_regression_threshold / 100.0
    if any(delta < -threshold for delta in result.deltas.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
```

## scripts/generate_api_docs.py

```python
"""CLI to export the FastAPI OpenAPI schema to disk."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.main import app  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate API documentation artifacts")
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "docs" / "api" / "openapi.json",
        help="Path to write the OpenAPI document (defaults to docs/api/openapi.json)",
    )
    parser.add_argument(
        "--format",
        choices=("json", "yaml"),
        default="json",
        help="Output format for the schema",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="Indentation for JSON output",
    )
    return parser


def export_schema(output_path: Path, output_format: str, indent: int = 2) -> None:
    schema = app.openapi()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_format == "json":
        payload = json.dumps(schema, indent=indent, sort_keys=True)
        output_path.write_text(payload + "\n", encoding="utf-8")
    else:
        payload = yaml.safe_dump(schema, sort_keys=False)
        output_path.write_text(payload, encoding="utf-8")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    export_schema(output_path=args.output, output_format=args.format, indent=args.indent)


if __name__ == "__main__":
    main()
```

## scripts/generate_env.py

```python
#!/usr/bin/env python3
"""Create or refresh the repository .env file.

Usage examples::

    python scripts/generate_env.py            # creates .env if missing
    python scripts/generate_env.py --force    # overwrite existing .env
    python scripts/generate_env.py --ignore-env   # ignore host env vars when writing
"""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path


def _fingerprint(value: str | None) -> str | None:
    if not value:
        return None
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


DEFAULTS = {
    # Core models
    "OPENAI_API_KEY": "sk-your-openai-key",
    "EMBED_MODEL": "text-embedding-3-large",
    "EMBEDDING_MODEL_VERSION": "text-embedding-3-large@2025-01-15",
    "GEN_MODEL": "gpt-4.1",
    "CONFIDENCE_THRESHOLD": "0.70",
    "CHUNK_TARGET_TOKENS": "512",
    "CHUNK_MIN_TOKENS": "256",
    "CHUNK_OVERLAP_TOKENS": "100",
    "MAX_CONTEXT_CHUNKS": "10",
    "ENABLE_RERANKER": "0",
    "TOP_K": "20",
    "EVAL_REGRESSION_THRESHOLD": "3.0",
    # Paths & storage
    "CONTENT_ROOT": "./content",
    "INDICES_DIR": "./indices",
    "LOG_PATH": "./logs/app.jsonl",
    "ERROR_LOG_PATH": "./logs/errors.jsonl",
    "DICTIONARY_PATH": "./indices/dictionary.json",
    # Database & vector search
    "DATABASE_URL": "postgresql://atticus:atticus@localhost:5432/atticus",
    "POSTGRES_DB": "atticus",
    "POSTGRES_USER": "atticus",
    "POSTGRES_PASSWORD": "atticus",
    "PGVECTOR_LISTS": "100",
    "PGVECTOR_PROBES": "4",
    # Logging & telemetry
    "LOG_LEVEL": "INFO",
    "LOG_VERBOSE": "0",
    "LOG_TRACE": "0",
    "LOG_FORMAT": "json",
    "TIMEZONE": "UTC",
    # Rate limiting
    "RATE_LIMIT_REQUESTS": "5",
    "RATE_LIMIT_WINDOW_SECONDS": "60",
    # Notifications & escalation
    "CONTACT_EMAIL": "atticus-contact@example.com",
    "SMTP_HOST": "smtp.example.com",
    "SMTP_PORT": "587",
    "SMTP_USER": "smtp-user",
    "SMTP_PASS": "change-me-smtp-password",
    "SMTP_FROM": "atticus-escalations@example.com",
    "SMTP_TO": "atticus-technical-support@example.com",
    "SMTP_DRY_RUN": "1",
    "EMAIL_SANDBOX": "true",
    "SMTP_ALLOW_LIST": "",
    # Auth & admin
    "AUTH_SECRET": "dev-secret",
    "NEXTAUTH_SECRET": "dev-secret",
    "NEXTAUTH_URL": "http://localhost:3000",
    "NEXTAUTH_URL_INTERNAL": "http://localhost:3000",
    "DEFAULT_ORG_ID": "org-atticus",
    "DEFAULT_ORG_NAME": "Atticus Default",
    "ADMIN_EMAIL": "admin@atticus.local",
    "ADMIN_NAME": "Atticus Admin",
    "ADMIN_API_TOKEN": "set-a-strong-admin-token",
    "AUTH_DEBUG_MAILBOX_DIR": "./logs/mailbox",
    # Local email sandbox
    "EMAIL_SERVER_HOST": "localhost",
    "EMAIL_SERVER_PORT": "1025",
    "EMAIL_SERVER_USER": "",
    "EMAIL_SERVER_PASSWORD": "",
    "EMAIL_FROM": "no-reply@atticus.local",
    # Frontend/API integration
    "RAG_SERVICE_URL": "http://localhost:8000",
    "ASK_SERVICE_URL": "http://localhost:8000",
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a .env file for Atticus")
    parser.add_argument("--force", action="store_true", help="overwrite an existing .env file")
    parser.add_argument(
        "--ignore-env",
        action="store_true",
        help="ignore host environment variables when populating values",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    env_path = root / ".env"

    if env_path.exists() and not args.force:
        print(f"[generate_env] .env already exists at {env_path}. Use --force to overwrite.")
        return 0

    if args.ignore_env:
        print("[generate_env] Ignoring host environment variables; writing defaults.")

    lines = []
    used_openai_key: str | None = None
    for k, v in DEFAULTS.items():
        if args.ignore_env:
            val = v
        else:
            val = os.environ.get(k, v)
        if isinstance(val, str):
            val = val.strip()
        if k == "OPENAI_API_KEY":
            used_openai_key = val
        lines.append(f"{k}={val}")

    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[generate_env] Wrote {env_path}")
    if used_openai_key:
        source = (
            "environment" if not args.ignore_env and "OPENAI_API_KEY" in os.environ else "defaults"
        )
        fingerprint = _fingerprint(used_openai_key) or "none"
        print(f"[generate_env] OPENAI_API_KEY resolved from {source} (fingerprint={fingerprint})")
    else:
        print(
            "[generate_env] Note: OPENAI_API_KEY is empty. Set it via environment before running, e.g.\n"
            "  PowerShell:  $env:OPENAI_API_KEY='sk-...' ; python scripts/generate_env.py --force\n"
            "  Bash:        OPENAI_API_KEY='sk-...' python scripts/generate_env.py --force"
        )
    if (
        not args.ignore_env
        and "OPENAI_API_KEY" in os.environ
        and os.environ.get("OPENAI_API_KEY", "").strip() != (used_openai_key or "")
    ):
        print(
            "[generate_env] Warning: host OPENAI_API_KEY differs from written value. Run with --ignore-env to bypass host overrides."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

## scripts/icon-audit.mjs

```javascript
#!/usr/bin/env node
import { readFileSync, readdirSync, statSync } from "node:fs";
import path from "node:path";

const TARGET_DIRECTORIES = ["app", "components"];
const ICON_IMPORT_REGEX = /import\s+{([^}]+)}\s+from\s+['"]lucide-react['"]/g;
const ICON_NAME_REGEX = /^[A-Z][A-Za-z0-9]*$/;

function walk(dir) {
  const entries = readdirSync(dir, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    if (entry.name.startsWith(".") || entry.name.startsWith("_")) continue;
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      files.push(...walk(fullPath));
    } else if (entry.isFile() && /\.(tsx|ts|jsx|js)$/.test(entry.name)) {
      files.push(fullPath);
    }
  }
  return files;
}

function auditFile(file) {
  const source = readFileSync(file, "utf8");
  const matches = [];
  let match;
  while ((match = ICON_IMPORT_REGEX.exec(source)) !== null) {
    matches.push({ importBlock: match[1], index: match.index });
  }
  const violations = [];
  for (const { importBlock, index } of matches) {
    const rawIcons = importBlock.split(",");
    for (const rawIcon of rawIcons) {
      const icon = rawIcon.trim();
      if (!icon) continue;
      const [name] = icon.split(/\s+as\s+/i);
      if (!ICON_NAME_REGEX.test(name)) {
        violations.push({ file, icon: name.trim(), position: index });
      }
    }
  }
  return violations;
}

const allViolations = [];
for (const dir of TARGET_DIRECTORIES) {
  if (!statSync(dir, { throwIfNoEntry: false })) {
    continue;
  }
  const files = walk(dir);
  for (const file of files) {
    allViolations.push(...auditFile(file));
  }
}

if (allViolations.length > 0) {
  console.error("Found invalid lucide-react icon imports:");
  for (const violation of allViolations) {
    console.error(`  ${violation.file}: ${violation.icon || "<empty>"}`);
  }
  process.exit(1);
}

console.log("Lucide icon imports look good.");
```

## scripts/ingest_cli.py

```python
#!/usr/bin/env python3
"""CLI entrypoint for the Atticus ingestion pipeline."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path

# Ensure repository root on import path when running as a script
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from atticus.config import load_settings  # noqa: E402
from ingest.pipeline import IngestionOptions, ingest_corpus  # noqa: E402


def _paths(value: Sequence[str] | None) -> list[Path] | None:
    if not value:
        return None
    return [Path(item).expanduser().resolve() for item in value]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Atticus ingestion pipeline")
    parser.add_argument(
        "--paths",
        nargs="*",
        help="Optional subset of files or directories to ingest",
    )
    parser.add_argument(
        "--full-refresh",
        action="store_true",
        help="Force reprocessing of all documents even if unchanged",
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to an alternate config.yaml file",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path to write the ingestion summary JSON",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.config:
        os.environ["CONFIG_PATH"] = str(args.config)

    settings = load_settings()
    options = IngestionOptions(full_refresh=bool(args.full_refresh), paths=_paths(args.paths))
    summary = ingest_corpus(settings=settings, options=options)
    payload = asdict(summary)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    else:
        print(json.dumps(payload, indent=2, default=str))


if __name__ == "__main__":
    main()
```

## scripts/list_make_targets.py

```python
"""List unique make targets defined in provided makefiles."""

from __future__ import annotations

import pathlib
import re
import sys


def collect_targets(paths: list[str]) -> list[str]:
    pattern = re.compile(r"^[A-Za-z0-9_.-]+:")
    targets: set[str] = set()
    for raw_path in paths:
        path = pathlib.Path(raw_path)
        if not path.exists():
            continue
        for line in path.read_text().splitlines():
            if pattern.match(line):
                name = line.split(":", 1)[0]
                if name != ".PHONY":
                    targets.add(name)
    return sorted(targets)


def main(argv: list[str]) -> int:
    targets = collect_targets(argv or ["Makefile"])
    for name in targets:
        print(name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
```

## scripts/make_seed.py

```python
"""Generate a lightweight seed manifest from the current CED corpus."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:  # pragma: no cover - optional dependency
    import pgvector.psycopg  # type: ignore
    import psycopg  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - lightweight fallback for seed generation
    import types

    psycopg = types.ModuleType("psycopg")
    psycopg.rows = types.SimpleNamespace(dict_row=None)
    psycopg.types = types.SimpleNamespace(json=types.SimpleNamespace(Json=lambda value: value))
    psycopg.connect = lambda *args, **kwargs: (_ for _ in ()).throw(
        RuntimeError("psycopg unavailable")
    )
    sys.modules.setdefault("psycopg", psycopg)

    pgvector = types.ModuleType("pgvector")
    sys.modules.setdefault("pgvector", pgvector)

    pgvector_psycopg = types.ModuleType("pgvector.psycopg")
    pgvector_psycopg.register_vector = lambda conn: None
    pgvector_psycopg.Vector = list
    sys.modules["pgvector.psycopg"] = pgvector_psycopg

    ingest_pkg = types.ModuleType("ingest")
    ingest_pkg.__path__ = [str(ROOT / "ingest")]
    sys.modules.setdefault("ingest", ingest_pkg)

    sys.modules.setdefault("camelot", types.SimpleNamespace(read_pdf=lambda *args, **kwargs: []))
    sys.modules.setdefault("tabula", types.SimpleNamespace(read_pdf=lambda *args, **kwargs: []))

from atticus.config import load_settings
from atticus.utils import sha256_file
from ingest.chunker import chunk_document
from ingest.parsers import discover_documents, parse_document


def build_seed_manifest() -> list[dict[str, object]]:
    settings = load_settings()
    settings.ensure_directories()
    manifest: list[dict[str, object]] = []
    for index, path in enumerate(discover_documents(settings.content_dir)):
        document = parse_document(path)
        document.sha256 = sha256_file(path)
        chunks = chunk_document(document, settings)
        manifest.append(
            {
                "document": str(path),
                "sha256": document.sha256,
                "source_type": document.source_type,
                "chunk_count": len(chunks),
                "chunks": [
                    {
                        "chunk_id": chunk.chunk_id,
                        "sha256": chunk.sha256,
                        "heading": chunk.heading,
                        "chunking": chunk.extra.get("chunking"),
                        "page_number": chunk.page_number,
                    }
                    for chunk in chunks[:25]
                ],
            }
        )
        if index >= 9:  # keep seed small
            break
    return manifest


def main() -> None:
    output_path = Path("seeds/seed_manifest.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    manifest = build_seed_manifest()
    output_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote seed manifest with {len(manifest)} documents to {output_path}")


if __name__ == "__main__":
    main()
```

## scripts/rollback.md

```markdown
# Rollback Runbook (§7)

1. **Identify the prior release tag.**

   ```bash
   git fetch --tags
   git tag --sort=-creatordate | head
   ```

2. **Checkout the previous release.**

   ```bash
   git checkout <previous-tag>
   ```

3. **Restore the matching index snapshot.**
   - Locate the snapshot in `indexes/snapshots/` stamped with the release timestamp.
   - Copy it over the active index:

     ```bash
     cp indexes/snapshots/<snapshot>.json indexes/atticus_index.json
     ```

4. **Re-pin configuration.**
   - Verify `pyproject.toml` matches the target tag.
   - Confirm embedding/LLM identifiers (`text-embedding-3-large`, `gpt-4.1`) in `atticus/config.py`.
5. **Smoke test with gold queries.**

   ```bash
   pytest evaluation/harness -k retrieval --maxfail=1
   ```

   Review `evaluation/runs/YYYYMMDD/` outputs for the top queries (nDCG@10, Recall@50, MRR).

6. **Log the rollback.**
   - Append the action to `CHANGELOG.md`.
   - Tag the rollback release (e.g., `v0.1.0-rollback1`) with a short summary of the trigger and outcome.
```

## scripts/rollback.py

```python
"""Restore the Atticus index to a previous snapshot."""

from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path

from atticus.config import AppSettings, load_manifest, load_settings, write_manifest
from atticus.logging import configure_logging, log_event
from atticus.vector_db import PgVectorRepository, load_metadata
from eval.runner import load_gold_set
from retriever.vector_store import VectorStore

SNAPSHOT_METADATA = "index_metadata.json"
SNAPSHOT_MANIFEST = "manifest.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rollback Atticus vector index")
    parser.add_argument(
        "--snapshot", type=Path, default=None, help="Specific snapshot directory to restore"
    )
    parser.add_argument("--skip-smoke", action="store_true", help="Skip smoke tests after rollback")
    parser.add_argument(
        "--limit", type=int, default=20, help="Number of gold queries for smoke testing"
    )
    parser.add_argument("--config", type=Path, help="Path to an alternate config.yaml")
    return parser.parse_args()


def _latest_snapshot_dir(directory: Path) -> Path:
    candidates = sorted([path for path in directory.iterdir() if path.is_dir()])
    if not candidates:
        raise FileNotFoundError(f"No snapshots found in {directory}")
    return candidates[-1]


def _run_smoke_tests(settings: AppSettings, logger, limit: int) -> list[str]:
    store = VectorStore(settings, logger)
    gold_examples = load_gold_set(settings.gold_set_path)[:limit]
    missing: list[str] = []
    for example in gold_examples:
        results = store.search(example.question, top_k=5)
        if not results:
            missing.append(example.question)
    return missing


def main() -> None:
    args = parse_args()
    if args.config:
        os.environ["CONFIG_PATH"] = str(args.config)
    settings = load_settings()
    logger = configure_logging(settings)

    if not settings.database_url:
        raise ValueError("DATABASE_URL must be configured before running rollback")

    snapshot_dir = args.snapshot or _latest_snapshot_dir(settings.snapshots_dir)
    metadata_path = snapshot_dir / SNAPSHOT_METADATA
    manifest_path = snapshot_dir / SNAPSHOT_MANIFEST
    if not metadata_path.exists() or not manifest_path.exists():
        raise FileNotFoundError(
            f"Snapshot {snapshot_dir} is missing {SNAPSHOT_METADATA} or {SNAPSHOT_MANIFEST}"
        )

    snapshot_manifest = load_manifest(manifest_path)
    if snapshot_manifest is None:
        raise FileNotFoundError(f"Snapshot manifest {manifest_path} is invalid or missing")

    chunks = load_metadata(metadata_path)
    repository = PgVectorRepository(settings)
    repository.ensure_schema()
    repository.truncate()

    documents = snapshot_manifest.documents
    ingest_time = snapshot_manifest.created_at

    chunks_by_document: dict[str, list] = {}
    for chunk in chunks:
        entry = chunks_by_document.setdefault(chunk.document_id, [])
        entry.append(chunk)

    for document_id, doc_chunks in chunks_by_document.items():
        if not doc_chunks:
            continue
        source_path = doc_chunks[0].source_path
        metadata = documents.get(source_path, {})
        repository.replace_document(
            document_id=document_id,
            source_path=source_path,
            sha256=str(metadata.get("sha256", "")),
            source_type=metadata.get("source_type"),
            chunks=doc_chunks,
            ingest_time=ingest_time,
        )

    shutil.copy2(metadata_path, settings.metadata_path)
    shutil.copy2(manifest_path, settings.manifest_path)

    restored_manifest = load_manifest(settings.manifest_path)
    if restored_manifest is None:
        write_manifest(settings.manifest_path, snapshot_manifest)
        restored_manifest = snapshot_manifest

    log_event(
        logger,
        "rollback_restored",
        snapshot=str(snapshot_dir),
        chunk_count=len(chunks),
        document_count=len(restored_manifest.documents),
    )

    if args.skip_smoke:
        print("Rollback complete. Smoke tests skipped.")
        return

    missing = _run_smoke_tests(settings, logger, args.limit)
    if missing:
        print("Rollback completed, but some queries returned no results:")
        for query in missing:
            print(f"  - {query}")
        print("Investigate the restored index before releasing.")
    else:
        print("Rollback validated successfully. All smoke tests returned results.")
    print("Tag the rollback commit and update CHANGELOG.md with details.")


if __name__ == "__main__":
    main()
```

## scripts/route-audit.mjs

```javascript
#!/usr/bin/env node
import { readdirSync, statSync } from "node:fs";
import path from "node:path";

const appDir = path.resolve("app");

function walkRoutes(current, prefix = "") {
  const entries = readdirSync(current, { withFileTypes: true });
  const result = [];
  for (const entry of entries) {
    if (entry.name.startsWith("_") || entry.name.startsWith(".")) continue;
    const fullPath = path.join(current, entry.name);
    const routePath = path.join(prefix, entry.name);
    if (entry.isDirectory()) {
      const isRouteSegment = ["page.tsx", "route.ts", "layout.tsx"].some((file) => {
        try {
          return statSync(path.join(fullPath, file)).isFile();
        } catch (error) {
          return false;
        }
      });
      if (isRouteSegment) {
        result.push({ segment: routePath.replace(/\\/g, "/"), files: readdirSync(fullPath) });
      }
      result.push(...walkRoutes(fullPath, routePath));
    }
  }
  return result;
}

const routes = walkRoutes(appDir);
console.log(JSON.stringify({ routes }, null, 2));
```

## scripts/run_ingestion.py

```python
#!/usr/bin/env python3
"""Legacy wrapper for the Atticus ingestion CLI."""

from __future__ import annotations

import runpy
from pathlib import Path


def main() -> None:
    target = Path(__file__).with_name("ingest_cli.py")
    runpy.run_path(str(target), run_name="__main__")


if __name__ == "__main__":
    main()
```

## scripts/smtp_test.py

```python
"""Manual SMTP smoke test used by `make smtp-test`."""

from __future__ import annotations

import sys

try:
    from atticus.notify.mailer import send_escalation
except Exception as exc:  # pragma: no cover - import is optional for devs
    IMPORT_ERROR = exc
    send_escalation = None
else:
    IMPORT_ERROR = None


def main() -> None:
    if send_escalation is None:
        print("SMTP mailer is unavailable: atticus.notify.mailer could not be imported.")
        if IMPORT_ERROR:
            print(f"Reason: {IMPORT_ERROR}")
        sys.exit(1)

    send_escalation("Atticus SMTP test", "This is a test from make smtp-test")
    print("smtp ok")


if __name__ == "__main__":
    main()
```

## scripts/test_health.py

```python
from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.main import app  # noqa: E402


def main() -> None:
    with TestClient(app) as client:
        res = client.get("/health")
        print("status:", res.status_code)
        print("json:", res.json())


if __name__ == "__main__":
    main()
```

## scripts/verify_pgvector.sql

```sql
-- Accept overrides via `psql -v expected_pgvector_dimension=1536 -v expected_pgvector_lists=50 ...`
\set ON_ERROR_STOP on

\if :{?expected_pgvector_dimension}
\else
  \set expected_pgvector_dimension 3072
\endif

\if :{?expected_pgvector_lists}
\else
  \set expected_pgvector_lists 100
\endif

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector') THEN
    RAISE EXCEPTION 'pgvector extension not installed';
  END IF;
END$$;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'atticus_documents') THEN
    RAISE EXCEPTION 'atticus_documents table missing';
  END IF;

  IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'atticus_chunks') THEN
    RAISE EXCEPTION 'atticus_chunks table missing';
  END IF;
END$$;

-- Validate embedding dimension matches expected setting (defaults to 3072).
DO $$
DECLARE
  dimension integer;
  expected integer := :expected_pgvector_dimension;
BEGIN
  SELECT atttypmod INTO dimension
  FROM pg_attribute
  WHERE attrelid = 'atticus_chunks'::regclass
    AND attname = 'embedding'
    AND NOT attisdropped;

  IF dimension IS NULL THEN
    RAISE EXCEPTION 'atticus_chunks.embedding column missing';
  END IF;

  IF dimension <> expected THEN
    RAISE EXCEPTION 'atticus_chunks.embedding dimension is %, expected %', dimension, expected;
  END IF;
END$$;

-- Confirm IVFFlat index exists for cosine search.
DO $$
DECLARE
  idx_record TEXT;
  expected_lists INTEGER := :expected_pgvector_lists;
  dimension INTEGER;
BEGIN
  SELECT atttypmod INTO dimension
  FROM pg_attribute
  WHERE attrelid = 'atticus_chunks'::regclass
    AND attname = 'embedding'
    AND NOT attisdropped;

  IF dimension IS NULL THEN
    RAISE EXCEPTION 'atticus_chunks.embedding column missing';
  END IF;

  IF dimension > 2000 THEN
    RAISE NOTICE 'Skipping IVFFlat verification because dimension % exceeds 2000. Install a pgvector build with higher INDEX_MAX_DIMENSIONS to enable ANN indexing.', dimension;
    RETURN;
  END IF;

  SELECT indexdef INTO idx_record
  FROM pg_indexes
  WHERE tablename = 'atticus_chunks'
    AND indexname = 'idx_atticus_chunks_embedding';

  IF idx_record IS NULL THEN
    RAISE EXCEPTION 'IVFFlat index missing on atticus_chunks';
  END IF;

  IF position(lower(format('lists = %s', expected_lists)) IN lower(idx_record)) = 0 THEN
    RAISE EXCEPTION 'idx_atticus_chunks_embedding lists mismatch. Expected lists=% with index definition: %', expected_lists, idx_record;
  END IF;
END$$;

-- Confirm metadata defaults are applied so ingestion can omit the column explicitly.
DO $$
DECLARE
  doc_default TEXT;
  chunk_default TEXT;
BEGIN
  SELECT column_default INTO doc_default
  FROM information_schema.columns
  WHERE table_name = 'atticus_documents' AND column_name = 'metadata';

  IF doc_default IS DISTINCT FROM '\''{}\''::jsonb' THEN
    RAISE NOTICE 'atticus_documents.metadata default is %, expected {}::jsonb', doc_default;
  END IF;

  SELECT column_default INTO chunk_default
  FROM information_schema.columns
  WHERE table_name = 'atticus_chunks' AND column_name = 'metadata';

  IF chunk_default IS DISTINCT FROM '\''{}\''::jsonb' THEN
    RAISE NOTICE 'atticus_chunks.metadata default is %, expected {}::jsonb', chunk_default;
  END IF;
END$$;

SELECT 'pgvector verification completed successfully.' AS status;
```

