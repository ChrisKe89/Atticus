# Code Bundle Generator

This file contains a single-script utility (PowerShell) to scan the repository and generate a combined Markdown bundle of all relevant code, Markdown, and JSON files. It excludes logs, build artifacts, caches, binaries, and other non-source outputs.

Quick start:

- From the repo root, run this in PowerShell 7+ (`pwsh`):
  - Copy the script block below into your terminal, or
  - Copy it into a file (e.g., `combine-code.ps1`) and run `pwsh -File combine-code.ps1`.

Output:

- Creates `ALL_CODE.md` at the repo root by default. You can change the output path with `-Output`.

Script:

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
  return
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
  $lines.Add("- `" + $rel.Replace('`','``') + "`")
}
$lines.Add("")

# Append each file content with fenced code blocks
foreach ($f in $files) {
  $rel = [IO.Path]::GetRelativePath($Root, $f.FullName)
  $ext = $f.Extension.ToLowerInvariant()
  $lang = if ($f.Name -match '^Dockerfile(\..+)?$') { 'dockerfile' } else { $langMap[$ext] }
  if (-not $lang) { $lang = 'text' }
  Write-Info "Bundling: $rel"

  $content = Get-Content -Path $f.FullName -Raw -Encoding UTF8
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

Notes:

- Edit the `$includeExt`, `$excludeDirs`, and `$excludeNamePatterns` lists in the script to tweak what’s included.
- The script intentionally skips large files (> 5MB), minified assets, lockfiles, images, and binaries.
- `.vscode/*.json` will be included (useful editor configs), while typical build outputs and caches are excluded.

