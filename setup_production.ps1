# =================================
# ZYGOTRIP PRODUCTION BOOTSTRAP
# =================================

Write-Host "Starting Production Setup..." -ForegroundColor Cyan

# ---------- Install PostgreSQL ----------
$pgInstaller = "$env:TEMP\postgresql.exe"

Write-Host "Downloading PostgreSQL..."
Invoke-WebRequest https://get.enterprisedb.com/postgresql/postgresql-16.2-1-windows-x64.exe -OutFile $pgInstaller

Write-Host "Installing PostgreSQL silently..."
Start-Process -Wait -FilePath $pgInstaller -ArgumentList "--mode unattended --superpassword postgres"

$env:Path += ";C:\Program Files\PostgreSQL\16\bin"

Start-Sleep -Seconds 10

# ---------- Create DB ----------
Write-Host "Creating database..."
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -h localhost -c "CREATE DATABASE zygotrip;" 2>$null
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -h localhost -d zygotrip -c "CREATE EXTENSION IF NOT EXISTS pg_trgm;"

# ---------- Install Python deps ----------
Write-Host "Installing dependencies..."
pip install psycopg2-binary redis django-filter

# ---------- Patch settings ----------
Write-Host "Updating Django DB config..."

$settingsPath = "zygotrip_project/settings.py"
$content = Get-Content $settingsPath -Raw

$dbBlock = @"
DATABASES = {
 'default': {
     'ENGINE': 'django.db.backends.postgresql',
     'NAME': 'zygotrip',
     'USER': 'postgres',
     'PASSWORD': 'postgres',
     'HOST': 'localhost',
     'PORT': '5432',
 }
}
"@

$content = [regex]::Replace($content,"DATABASES\s*=\s*\{[\s\S]*?\}",$dbBlock)
Set-Content $settingsPath $content

# ---------- Remove SQLite ----------
if (Test-Path "db.sqlite3") {
    Remove-Item db.sqlite3
}

# ---------- Migrate ----------
Write-Host "Running migrations..."
python manage.py migrate

# ---------- Init Scores ----------
Write-Host "Initializing ranking signals..."
python manage.py shell -c "
from hotels.models import Property
for p in Property.objects.all():
    p.search_score = (p.rating or 3.5)*20
    p.save()
print('Done')
"

# ---------- Create Admin ----------
Write-Host "Creating admin..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User=get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin','admin@test.com','admin123')
"

Write-Host ""
Write-Host "=================================" -ForegroundColor Green
Write-Host "SYSTEM READY" -ForegroundColor Green
Write-Host "Admin: admin / admin123" -ForegroundColor Green
Write-Host "Run: python manage.py runserver" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green
