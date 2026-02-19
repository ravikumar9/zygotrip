$ErrorActionPreference = "Stop"

Write-Host "=== BUILDING CLEAN AUDIT ZIP ==="

$root = Get-Location
$temp = Join-Path $root "AUDIT_TEMP"
$zip  = Join-Path $root "audit_package.zip"

Remove-Item $temp -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item $zip  -Force -ErrorAction SilentlyContinue

New-Item -ItemType Directory $temp | Out-Null

$include = @(
"templates","static","apps","core","hotels","buses","cabs","packages",
"accounts","payments","pricing","reviews","rooms","inventory","wallet",
"security","meals","promos","dashboard_admin","dashboard_owner",
"dashboard_finance","flights","trains","zygotrip_project"
)

foreach ($dir in $include) {
    $src = Join-Path $root $dir
    if (Test-Path $src) {
        Copy-Item $src -Destination $temp -Recurse -Force
        Write-Host "Copied $dir"
    }
}

$files = @("manage.py","requirements.txt","Dockerfile","docker-compose.yml")

foreach ($file in $files) {
    $src = Join-Path $root $file
    if (Test-Path $src) {
        Copy-Item $src $temp
        Write-Host "Copied $file"
    }
}

Write-Host "Cleaning junk..."

Get-ChildItem $temp -Recurse -Force |
Where-Object {
    $_.FullName -match "__pycache__|\.pyc$|\.pyo$|\.log$|\.sqlite3$|\.rdb$|\.ps1$"
} | Remove-Item -Force -Recurse

Write-Host "Creating ZIP..."

Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::CreateFromDirectory($temp,$zip)

Remove-Item $temp -Recurse -Force

if (Test-Path $zip) {
    Write-Host ""
    Write-Host "SUCCESS → $zip"
} else {
    Write-Host "FAILED → ZIP not created"
}
