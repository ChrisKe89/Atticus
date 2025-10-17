# Utility: concatenate repository files into a single Markdown bundle.
# Usage: pwsh -File scripts/dump_all_files.ps1 [-Output ALL_FILES_FULL.md] [-MaxKB 400]

[CmdletBinding()]
param(
    [string]$Output = "ALL_FILES_FULL.md",
    [int]$MaxKB = 400
)

$root = (Get-Location).ProviderPath
$sizeLimitBytes = $MaxKB * 1024
$encoding = [System.Text.Encoding]::UTF8

$excludeDirNames = @(
    ".git", ".github", ".next", ".venv", ".pytest_cache", ".ruff_cache", ".mypy_cache",
    "node_modules", "dist", "build", "coverage", "reports", "eval", "_backup"
)
$excludeExt = @(
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".zip", ".7z", ".rar", ".jar",
    ".exe", ".dll", ".pdb", ".wasm", ".map", ".lock", ".tsbuildinfo", ".woff",
    ".woff2", ".ttf", ".eot"
)
$includeExt = @(
    ".md", ".mdx", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".json", ".jsonc",
    ".yml", ".yaml", ".toml", ".ini", ".cfg", ".conf", ".py", ".ps1", ".psm1", ".sh",
    ".bash", ".zsh", ".fish", ".bat", ".cmd", ".sql", ".prisma", ".html", ".htm",
    ".css", ".scss", ".env", ".dockerfile", ".txt", ".cs", ".java"
)
$includeNames = @("Dockerfile", "Makefile", ".env", ".env.example")

$langMap = @{
    ".ts" = "ts"; ".tsx" = "tsx"; ".js" = "js"; ".jsx" = "jsx"; ".mjs" = "js"; ".cjs" = "js";
    ".py" = "python"; ".ps1" = "powershell"; ".psm1" = "powershell"; ".sh" = "bash";
    ".bash" = "bash"; ".zsh" = "bash"; ".fish" = "fish"; ".bat" = "bat"; ".cmd" = "bat";
    ".yml" = "yaml"; ".yaml" = "yaml"; ".json" = "json"; ".jsonc" = "jsonc"; ".toml" = "toml";
    ".ini" = "ini"; ".cfg" = "ini"; ".conf" = "ini"; ".md" = "markdown"; ".mdx" = "markdown";
    ".txt" = "text"; ".css" = "css"; ".scss" = "scss"; ".html" = "html"; ".htm" = "html";
    ".sql" = "sql"; ".prisma" = "prisma"; ".dockerfile" = "dockerfile"; ".env" = "properties"
}

function Get-RelativePath([string]$fullPath) {
    if ($fullPath.StartsWith($root, [System.StringComparison]::OrdinalIgnoreCase)) {
        return $fullPath.Substring($root.Length).TrimStart('\', '/')
    }
    return $fullPath
}

function Should-Exclude([string]$relativePath) {
    $segments = $relativePath -split '[\\/]' | Where-Object { $_ -ne "" }
    foreach ($segment in $segments) {
        if ($excludeDirNames -contains $segment) { return $true }
        if ($segment -like "_backup*") { return $true }
    }
    return $false
}

function Get-Language([System.IO.FileInfo]$file) {
    $ext = $file.Extension.ToLowerInvariant()
    if (-not $ext -and $file.Name.Equals("Dockerfile", "OrdinalIgnoreCase")) {
        return "dockerfile"
    }
    return $langMap[$ext]
}

$outputPath = Join-Path $root $Output
if (Test-Path $outputPath) {
    Remove-Item $outputPath -Force
}

$files = Get-ChildItem -Recurse -File | Where-Object {
    $rel = Get-RelativePath $_.FullName
    if (-not $rel) { return $false }
    if ($rel -eq $Output) { return $false }
    if (Should-Exclude $rel) { return $false }

    $ext = $_.Extension.ToLowerInvariant()
    if ($excludeExt -contains $ext) { return $false }

    $inAllowList =
        ($includeExt -contains $ext) -or
        ($includeNames -contains $_.Name) -or
        ($ext -eq "" -and $includeNames -contains $_.Name)

    if (-not $inAllowList) { return $false }
    if ($_.Length -gt $sizeLimitBytes) { return $false }
    return $true
} | Sort-Object FullName

$included = 0
$skipped = New-Object System.Collections.Generic.List[string]

$writer = New-Object System.IO.StreamWriter($outputPath, $false, $encoding)
try {
    $headerLines = @(
        "# Atticus - FULL REPO DUMP",
        "",
        "Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz')",
        "Max file size: ${MaxKB}KB",
        "Excluded directories: $($excludeDirNames -join ', ')",
        "Excluded extensions: $($excludeExt -join ', ')",
        "",
        "---",
        ""
    )
    $headerLines | ForEach-Object { $writer.WriteLine($_) }

    foreach ($file in $files) {
        $relative = Get-RelativePath $file.FullName
        $lang = Get-Language $file

        try {
            $content = Get-Content -LiteralPath $file.FullName -Raw -ErrorAction Stop
        } catch {
            $skipped.Add("$relative :: $($_.Exception.Message)")
            continue
        }

        $writer.WriteLine()
        $writer.WriteLine("## $relative")
        $writer.WriteLine()
        $writer.WriteLine(("```{0}" -f $lang))
        $writer.Write($content)
        if (-not $content.EndsWith("`n")) { $writer.WriteLine() }
        $writer.WriteLine("```")
        $included++
    }

    $writer.WriteLine()
    $writer.WriteLine("---")
    $writer.WriteLine([string]::Format("Included files: {0}", $included))
    $writer.WriteLine([string]::Format("Skipped files: {0}", $skipped.Count))
    $writer.WriteLine()

    if ($skipped.Count -gt 0) {
        $writer.WriteLine("### Skipped (errors or filtered):")
        foreach ($item in $skipped) {
            $writer.WriteLine($item)
        }
        $writer.WriteLine()
    }
}
finally {
    $writer.Dispose()
}

Write-Host "Done. Created $Output with $included files (<= ${MaxKB}KB each)."
