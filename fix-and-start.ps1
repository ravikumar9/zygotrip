Write-Host ""
Write-Host "=== ZYGOTRIP AUTO FIX + START ===" -ForegroundColor Cyan
Write-Host ""

# Check docker
docker info > $null 2>&1
if ($LASTEXITCODE -ne 0){
    Write-Host "Docker not running. Start Docker Desktop first." -ForegroundColor Red
    exit
}

Write-Host "Docker running OK" -ForegroundColor Green


# Fix compose DB
$compose="docker-compose.yml"

if(!(Test-Path $compose)){
    Write-Host "docker-compose.yml missing" -ForegroundColor Red
    exit
}

$c=Get-Content $compose -Raw

if($c -notmatch "POSTGRES_DB"){
    Write-Host "Injecting DB name..." -ForegroundColor Yellow
    $c=$c -replace "POSTGRES_PASSWORD:.*","POSTGRES_PASSWORD: postgres`n      POSTGRES_DB: zygotrip_user"
    Set-Content $compose $c
}else{
    Write-Host "DB already configured"
}


# remove corrupted celery db
Write-Host "Cleaning scheduler..."
Get-ChildItem -Filter "celerybeat-schedule*" -ErrorAction SilentlyContinue | Remove-Item -Force


# reset containers
Write-Host "Resetting containers..."
docker compose down -v | Out-Null


# build
Write-Host "Building..."
docker compose build


# start
Write-Host "Starting stack..."
docker compose up -d

Start-Sleep 12


# check containers
$fail=0
$list=docker ps --format "{{.Names}}"

foreach($n in "postgres","redis","worker","beat","web","nginx"){
    if($list -match $n){
        Write-Host "[OK] $n running" -ForegroundColor Green
    }else{
        Write-Host "[FAIL] $n missing" -ForegroundColor Red
        $fail++
    }
}


# http check
try{
    Invoke-WebRequest http://localhost -UseBasicParsing -TimeoutSec 5 | Out-Null
    Write-Host "[OK] Site responding" -ForegroundColor Green
}catch{
    Write-Host "[FAIL] Site not responding" -ForegroundColor Red
    $fail++
}


Write-Host ""
Write-Host "=========================="

if($fail -eq 0){
    Write-Host "SYSTEM READY FOR TESTING" -ForegroundColor Green
}else{
    Write-Host "SYSTEM FAILED — LOGS BELOW" -ForegroundColor Red
    docker compose logs --tail 40
}

Write-Host "=========================="
Write-Host ""
