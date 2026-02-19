Write-Host "==== FULL UI AUTO FIX START ===="

# ---------- CLEAN NODE ----------
if (Test-Path node_modules) { Remove-Item node_modules -Recurse -Force }
if (Test-Path package-lock.json) { Remove-Item package-lock.json -Force }

npm cache clean --force

# ---------- INSTALL DEPS ----------
npm install
npm install -D tailwindcss postcss autoprefixer

# ---------- ENSURE FOLDERS ----------
if (!(Test-Path "src")) { New-Item -ItemType Directory src }
if (!(Test-Path "static/css")) { New-Item -ItemType Directory static/css -Force }

# ---------- CREATE INPUT.CSS ----------
$inputCss = @"
@tailwind base;
@tailwind components;
@tailwind utilities;
"@

Set-Content src/input.css $inputCss

# ---------- INIT CONFIG IF MISSING ----------
if (!(Test-Path "tailwind.config.js")) {
    npx tailwindcss init -p
}

# ---------- BUILD CSS ----------
npx tailwindcss -i ./src/input.css -o ./static/css/tailwind.css --minify

Write-Host "==== UI BUILD COMPLETE ===="
