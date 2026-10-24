# Copies the project starter into a new or existing project folder.
# Never overwrites a file that already exists; it lists those instead.
# Usage: .\new-project.ps1 -Path "C:\Proiecte\aplicatia-mea" [-Name "Aplicatia mea"] [-NoGit]
param(
  [string]$Path,
  [string]$Name,
  [switch]$NoGit
)

$ErrorActionPreference = 'Stop'
$starter = Join-Path $PSScriptRoot 'project-starter'
if (-not (Test-Path $starter)) { throw "Nu gasesc mapa project-starter langa script: $starter" }

if (-not $Path) { $Path = Read-Host 'Calea mapei proiectului (ex. C:\Proiecte\aplicatia-mea)' }
$Path = $Path.Trim('"', ' ')
if (-not $Path) { throw 'Nu ai scris nicio cale.' }
if (-not (Test-Path $Path)) { New-Item -ItemType Directory -Path $Path | Out-Null }
$target = (Resolve-Path $Path).Path
if (-not $Name) { $Name = Split-Path $target -Leaf }

$utf8 = New-Object System.Text.UTF8Encoding($false)
$copied = @(); $skipped = @()

Get-ChildItem $starter -Recurse -File -Force | ForEach-Object {
  $rel = $_.FullName.Substring($starter.Length + 1)
  $dest = Join-Path $target $rel
  if ($rel -eq '.gitignore' -and (Test-Path $dest)) {
    # Existing .gitignore: add only the lines it doesn't have yet.
    $have = Get-Content $dest
    $missing = Get-Content $_.FullName | Where-Object { $_ -and -not $_.StartsWith('#') -and ($have -notcontains $_) }
    if ($missing) {
      Add-Content -Path $dest -Value (@('', '# Added by project starter') + $missing) -Encoding utf8
      $copied += "$rel (adaugat $($missing.Count) randuri)"
    } else { $skipped += $rel }
    return
  }
  if (Test-Path $dest) { $skipped += $rel; return }
  New-Item -ItemType Directory -Force -Path (Split-Path $dest) | Out-Null
  if ($_.Extension -eq '.md') {
    $text = [IO.File]::ReadAllText($_.FullName, $utf8).Replace('<project name>', $Name)
    [IO.File]::WriteAllText($dest, $text, $utf8)
  } else {
    Copy-Item $_.FullName $dest
  }
  $copied += $rel
}

$gitMsg = ''
if (-not $NoGit -and -not (Test-Path (Join-Path $target '.git')) -and (Get-Command git -ErrorAction SilentlyContinue)) {
  git -C $target init -q -b main
  $gitMsg = 'Am pornit git in mapa (ramura main).'
}

Write-Host ''
Write-Host "Gata: $target" -ForegroundColor Green
Write-Host "Copiate: $($copied.Count) fisiere"
$copied | ForEach-Object { Write-Host "  + $_" }
if ($skipped) {
  Write-Host "Existau deja, nu le-am atins: $($skipped.Count)" -ForegroundColor Yellow
  $skipped | ForEach-Object { Write-Host "  = $_" }
}
if ($gitMsg) { Write-Host $gitMsg }
$claudeMd = Join-Path $target 'CLAUDE.md'
if (($skipped -contains 'CLAUDE.md') -and -not (Select-String -Path $claudeMd -Pattern '@AGENTS.md' -SimpleMatch -Quiet)) {
  Write-Host 'Atentie: CLAUDE.md exista deja si nu importa AGENTS.md. Adauga pe primul rand: @AGENTS.md' -ForegroundColor Yellow
}
Write-Host ''
Write-Host 'Pasul urmator: deschide mapa in Claude Code. La primul mesaj, Claude completeaza singur AGENTS.md.'
