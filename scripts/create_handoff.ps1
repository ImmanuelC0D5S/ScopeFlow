param(
  [string]$OutputPath = "handoff.md"
)

$templatePath = "docs/handoff_prompt.md"
if (-not (Test-Path -LiteralPath $templatePath)) {
  throw "Missing template: $templatePath"
}

$template = Get-Content -Raw -LiteralPath $templatePath
$header = "# Handoff Document`nGenerated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz')`n`n"
Set-Content -LiteralPath $OutputPath -Value ($header + $template) -Encoding UTF8
Write-Output "Wrote $OutputPath"
