Write-Host "STARTING FIX..." -ForegroundColor Cyan

$templates = "templates"

if (!(Test-Path $templates)) {
    Write-Host "templates folder not found" -ForegroundColor Red
    exit
}

# ------------------------------------------------
# FIX 1 — HEADER LINKS
# ------------------------------------------------
$header = Get-ChildItem $templates -Recurse -Filter site_header.html | Select-Object -First 1

if ($header) {
    $text = Get-Content $header.FullName -Raw

    if ($text -notlike "*Flights*") {
        Write-Host "Fixing header..."

        $nav = @(
'<nav class="bg-white border-b">',
'<div class="max-w-7xl mx-auto px-4 py-3 flex justify-between">',
'<a href="/" class="font-bold text-lg text-indigo-600">Zygotrip</a>',
'<div class="space-x-6 text-sm">',
'<a href="/hotels/">Hotels</a>',
'<a href="/buses/">Buses</a>',
'<a href="/cabs/">Cabs</a>',
'<a href="/packages/">Packages</a>',
'<a href="/flights/">Flights</a>',
'<a href="/trains/">Trains</a>',
'{% if user.is_authenticated %}',
'<a href="/logout/">Logout</a>',
'{% else %}',
'<a href="/login/">Login</a>',
'<a href="/register/">Register</a>',
'{% endif %}',
'</div></div></nav>'
)

        $nav -join "`n" | Set-Content $header.FullName
    }
}

# ------------------------------------------------
# FIX 2 — GRADIENT BODY
# ------------------------------------------------
$base = "templates\base.html"

if (Test-Path $base) {
    $body = Get-Content $base -Raw

    if ($body -notlike "*bg-gradient*") {
        Write-Host "Applying gradient..."
        $body = $body -replace "<body.*?>", '<body class="min-h-screen bg-gradient-to-br from-indigo-500 via-purple-500 to-blue-500">'
        Set-Content $base $body
    }
}

# ------------------------------------------------
# FIX 3 — REMOVE DUPLICATE EMPTY TEXT
# ------------------------------------------------
Write-Host "Cleaning empty states..."

Get-ChildItem $templates -Recurse -Filter *.html | ForEach-Object {
    $lines = Get-Content $_.FullName
    $found = $false
    $out = @()

    foreach ($l in $lines) {
        if ($l -match "No results found") {
            if (!$found) {
                $out += $l
                $found = $true
            }
        }
        else {
            $out += $l
        }
    }

    $out | Set-Content $_.FullName
}

# ------------------------------------------------
# FIX 4 — TEST TEMPLATES
# ------------------------------------------------
Write-Host "Checking templates..."

python manage.py shell -c "from django.template.loader import get_template;import os
ok=True
for r,_,f in os.walk('templates'):
    for x in f:
        if x.endswith('.html'):
            p=os.path.join(r,x).replace('templates\\\\','').replace('\\\\','/')
            try:get_template(p)
            except Exception as e:print('ERROR:',p,e);ok=False
print('ALL OK' if ok else 'ERRORS FOUND')"

Write-Host ""
Write-Host "DONE." -ForegroundColor Green
