Write-Host "=== OTA UI HARD RESET START ==="

$root = Get-Location

function writeFile($path,$content){
    $full = Join-Path $root $path
    $dir = Split-Path $full
    if(!(Test-Path $dir)){ New-Item -ItemType Directory -Force -Path $dir | Out-Null }
    [System.IO.File]::WriteAllText($full,$content)
}

# --------------------------------------------------
# REMOVE OLD CSS
# --------------------------------------------------

$oldCss = @(
"static/css/design-system.css",
"static/css/layout.css",
"static/css/grid-system.css",
"static/css/old.css"
)

foreach($f in $oldCss){
    $p = Join-Path $root $f
    if(Test-Path $p){ Remove-Item $p -Force }
}

Write-Host "Old CSS removed"


# --------------------------------------------------
# CREATE CORE UI CSS
# --------------------------------------------------

$uiCss = @"
body{
margin:0;
font-family:Inter,Segoe UI,Arial;
background:#f6f7fb;
color:#222;
}

.ota-container{
max-width:1200px;
margin:auto;
padding:24px;
}

.hero{
background:linear-gradient(135deg,#ff7a18,#ffb347);
color:white;
text-align:center;
padding:70px 20px;
border-radius:0 0 20px 20px;
}

.grid{
display:grid;
gap:20px;
}

.grid-3{
grid-template-columns:repeat(auto-fit,minmax(260px,1fr));
}

.card{
background:white;
border-radius:14px;
padding:18px;
box-shadow:0 4px 18px rgba(0,0,0,.08);
transition:.2s;
}

.card:hover{
transform:translateY(-4px);
box-shadow:0 8px 26px rgba(0,0,0,.12);
}

.btn{
background:#ff6b2c;
color:white;
padding:10px 18px;
border-radius:8px;
display:inline-block;
text-decoration:none;
}

input,select{
height:46px;
padding:0 12px;
border-radius:8px;
border:1px solid #ddd;
width:100%;
}

.section{
margin-top:40px;
}
"@

writeFile "static/css/ota-ui.css" $uiCss
Write-Host "CSS system built"


# --------------------------------------------------
# BASE TEMPLATE
# --------------------------------------------------

$baseHtml = @"
<!DOCTYPE html>
<html>
<head>
<title>Zygotrip</title>
<link rel='stylesheet' href='/static/css/ota-ui.css'>
</head>
<body>

{% block hero %}{% endblock %}

<div class='ota-container'>
{% block content %}{% endblock %}
</div>

</body>
</html>
"@

writeFile "templates/base.html" $baseHtml
Write-Host "Base template normalized"


# --------------------------------------------------
# HOMEPAGE TEMPLATE
# --------------------------------------------------

$homepageHtml = @"
{% extends 'base.html' %}

{% block hero %}
<div class="hero">
<h1>Discover Your Perfect Journey</h1>
<p>Book hotels, buses, cabs & travel packages</p>
</div>
{% endblock %}

{% block content %}
<div class="section">

<h2>Popular Services</h2>

<div class="grid grid-3">

<div class="card">
<h3>Hotels</h3>
<a class="btn" href="/search/">Browse Hotels</a>
</div>

<div class="card">
<h3>Buses</h3>
<a class="btn">Find Buses</a>
</div>

<div class="card">
<h3>Cabs</h3>
<a class="btn">Book Cabs</a>
</div>

<div class="card">
<h3>Flights</h3>
<a class="btn">Search Flights</a>
</div>

</div>

</div>
{% endblock %}
"@

writeFile "templates/home.html" $homepageHtml
Write-Host "Homepage upgraded"


# --------------------------------------------------
# HOTEL CARD COMPONENT
# --------------------------------------------------

$hotelCard = @"
<div class='card'>
<h3>{{ hotel.name }}</h3>
<p>{{ hotel.city }}</p>
<h2>₹{{ hotel.price }}</h2>
<a class='btn' href='/hotels/{{ hotel.slug }}/'>View</a>
</div>
"@

writeFile "templates/components/hotel_card.html" $hotelCard
Write-Host "Hotel card component created"


# --------------------------------------------------
# SEARCH PAGE TEMPLATE
# --------------------------------------------------

$searchPage = @"
{% extends 'base.html' %}
{% block content %}

<h2>Search Results</h2>

{% if results %}
<div class='grid grid-3'>
{% for hotel in results %}
{% include 'components/hotel_card.html' %}
{% endfor %}
</div>
{% else %}
<p>No results found</p>
{% endif %}

{% endblock %}
"@

writeFile "templates/search/list.html" $searchPage
Write-Host "Search page normalized"


# --------------------------------------------------
# COLLECT STATIC
# --------------------------------------------------

python manage.py collectstatic --noinput | Out-Null

Write-Host ""
Write-Host "=== OTA UI SYSTEM INSTALLED SUCCESSFULLY ==="
Write-Host "Restart server now"
