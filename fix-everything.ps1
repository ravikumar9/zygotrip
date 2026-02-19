Write-Host "===== FULL ENVIRONMENT RESET + BUILD ====="

# ---------------- CLEAN ----------------
Write-Host "Cleaning node environment..."

if (Test-Path node_modules) {
    Remove-Item node_modules -Recurse -Force
}

if (Test-Path package-lock.json) {
    Remove-Item package-lock.json -Force
}

# ---------------- CACHE ----------------
Write-Host "Clearing npm cache..."
npm cache clean --force

# ---------------- INSTALL BASE ----------------
Write-Host "Installing base dependencies..."
npm install

# ---------------- TAILWIND ----------------
Write-Host "Installing Tailwind toolchain..."
npm install -D tailwindcss postcss autoprefixer

# ---------------- FIX PATH ----------------
Write-Host "Adding local binaries to PATH..."
$env:PATH += ";$PWD\node_modules\.bin"

# ---------------- CHECK CLI ----------------
Write-Host "Checking Tailwind CLI..."

$cli = Test-Path ".\node_modules\.bin\tailwindcss.cmd"

if (!$cli) {
    Write-Host "Tailwind CLI missing → Installing standalone version..."
    npm install -D tailwindcss@latest
}

# ---------------- INIT CONFIG ----------------
Write-Host "Initializing Tailwind config..."

if (!(Test-Path "tailwind.config.js")) {
    npx tailwindcss init -p
} else {
    Write-Host "Config already exists. Skipping init."
}

# ---------------- BUILD CSS ----------------
Write-Host "Building CSS..."

if (Test-Path ".\src\input.css") {
    npx tailwindcss -i ./src/input.css -o ./static/css/output.css --watch
} else {
    Write-Host "No src/input.css found. Skipping build step."
}

Write-Host "===== DONE ====="
