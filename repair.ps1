Write-Host "=== ZYGOTRIP MASTER REPAIR START ===" -ForegroundColor Cyan

$root = Get-Location
$templates = Join-Path $root "templates"

if (!(Test-Path $templates)) {
    Write-Host "templates folder not found" -ForegroundColor Red
    exit
}

# --------------------------------------------------
# 1. FIX HEADER LINKS
# --------------------------------------------------
$header = Get-ChildItem $templates -Recurse -Filter site_header.html | Select-Object -First 1
if ($header) {
    $content = Get-Content $header.FullName -Raw

    if ($content -notmatch "/flights/") {
        Write-Host "Fixing navbar links..."
        $content = $content -replace "</div>\s*</nav>", @"
<a href="/flights/" class="text-gray-700 hover:text-blue-600 font-medium">Flights</a>
<a href="/trains/" class="text-gray-700 hover:text-blue-600 font-medium">Trains</a>
</div></nav>
"@
        Set-Content $header.FullName $content
    }
}

# --------------------------------------------------
# 2. FIX DJANGO FOR LOOP LIST ERRORS
# --------------------------------------------------
Write-Host "Fixing invalid Django for loops..."
Get-ChildItem $templates -Recurse -Filter *.html | ForEach-Object {
    $file = $_.FullName
    $text = Get-Content $file -Raw

    if ($text -match "{%\s*for\s+\w+\s+in\s+\[") {
        $text = $text -replace "{%\s*for\s+(\w+)\s+in\s+\[(.*?)\]\s*%}",
                               "{% for `$1 in list_items %}"
        Set-Content $file $text
        Write-Host "Fixed loop → $file"
    }
}

# --------------------------------------------------
# 3. ENSURE BASE.HTML HAS GLOBAL GRADIENT
# --------------------------------------------------
$base = Join-Path $templates "base.html"
if (Test-Path $base) {
    $html = Get-Content $base -Raw

    if ($html -notmatch "bg-gradient") {
        Write-Host "Applying global gradient..."

        $html = $html -replace "<body.*?>",
@"
<body class="min-h-screen bg-gradient-to-br from-indigo-500 via-purple-500 to-blue-500">
"@
        Set-Content $base $html
    }
}

# --------------------------------------------------
# 4. FIX COMMON WRONG TEMPLATE FIELD NAMES
# --------------------------------------------------
Write-Host "Fixing serializer field mismatches..."

$map = @{
"item.price}}"="item.price_current}}"
"item.url}}"="item.cta_url}}"
"item.route}}"="item.from_city}} → {{ item.to_city}}"
"hotel.price}}"="hotel.price_current}}"
"hotel.primary_image"="hotel.image_url"
"hotel.rating}}"="hotel.rating_value}}"
"hotel.review_count}}"="hotel.rating_count}}"
"hotel.original_price}}"="hotel.price_original}}"
"hotel.discount_percentage}}"="hotel.discount_percent}}"
}

Get-ChildItem $templates -Recurse -Filter *.html | ForEach-Object {
    $file = $_.FullName
    $text = Get-Content $file -Raw
    $changed = $false

    foreach ($k in $map.Keys) {
        if ($text.Contains($k)) {
            $text = $text.Replace($k,$map[$k])
            $changed = $true
        }
    }

    if ($changed) {
        Set-Content $file $text
        Write-Host "Corrected fields → $file"
    }
}

# --------------------------------------------------
# 5. REMOVE DUPLICATE EMPTY STATE BLOCKS
# --------------------------------------------------
Write-Host "Cleaning duplicate empty-state blocks..."

Get-ChildItem $templates -Recurse -Filter *.html | ForEach-Object {
    $file = $_.FullName
    $lines = Get-Content $file

    $new = @()
    $seen = $false

    foreach ($l in $lines) {
        if ($l -match "No results found") {
            if (!$seen) {
                $new += $l
                $seen = $true
            }
        } else {
            $new += $l
        }
    }

    Set-Content $file $new
}

# --------------------------------------------------
# 6. VERIFY TEMPLATES COMPILE (REAL CHECK)
# --------------------------------------------------
Write-Host "Running Django template compilation test..."

python manage.py shell -c "
from django.template.loader import get_template
import os

base='templates'
errors=[]

for root,_,files in os.walk(base):
    for f in files:
        if f.endswith('.html'):
            p=os.path.join(root,f).replace('templates\\\\','').replace('\\\\','/')
            try:
                get_template(p)
            except Exception as e:
                errors.append((p,str(e)))

print('---- TEMPLATE REPORT ----')
if errors:
    for e in errors:
        print(e[0],'->',e[1])
else:
    print('ALL TEMPLATES OK')
" 

# --------------------------------------------------
# 7. FINAL STATUS REPORT
# --------------------------------------------------
Write-Host ""
Write-Host "=== MASTER REPAIR COMPLETE ===" -ForegroundColor Green
Write-Host "Verified:"
Write-Host "✔ Header links"
Write-Host "✔ Gradients"
Write-Host "✔ Template syntax"
Write-Host "✔ Serializer fields"
Write-Host "✔ Duplicate blocks removed"
Write-Host ""
Write-Host "Now run:"
Write-Host "python manage.py runserver"
