Write-Host "`n=== ZYGOTRIP AUTO DEPLOY ===" -ForegroundColor Cyan

if (!(Get-Command docker -ErrorAction SilentlyContinue)) {
 Write-Host "Docker not installed" -ForegroundColor Red
 exit
}

Write-Host "Building containers..."
docker compose build

Write-Host "Starting services..."
docker compose up -d

Start-Sleep 10

$fail=0
$containers=docker ps --format "{{.Names}}"

foreach($n in "db","redis","web","worker","beat","nginx"){
 if($containers -match $n){
  Write-Host "[OK] $n running" -ForegroundColor Green
 }else{
  Write-Host "[FAIL] $n missing" -ForegroundColor Red
  $fail++
 }
}

try{
 Invoke-WebRequest http://localhost -UseBasicParsing -TimeoutSec 5 | Out-Null
 Write-Host "[OK] Web responding" -ForegroundColor Green
}catch{
 Write-Host "[FAIL] Web not responding" -ForegroundColor Red
 $fail++
}

Write-Host "======================"

if($fail -eq 0){
 Write-Host "SYSTEM READY FOR MANUAL TESTING" -ForegroundColor Green
}else{
 Write-Host "SYSTEM FAILED — CHECK LOGS" -ForegroundColor Red
 docker compose logs
}

Write-Host "======================"
