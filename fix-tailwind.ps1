Write-Host "Cleaning node environment..."

if (Test-Path "node_modules") {
    Remove-Item "node_modules" -Recurse -Force
}

if (Test-Path "package-lock.json") {
    Remove-Item "package-lock.json" -Force
}

Write-Host "Clearing npm cache..."
npm cache clean --force

Write-Host "Reinstalling dependencies..."
npm install

Write-Host "Installing Tailwind toolchain..."
npm install -D tailwindcss@latest postcss autoprefixer

Write-Host "Checking Tailwind binary..."

$tailwindPath = ".\node_modules\.bin\tailwindcss.cmd"

if (!(Test-Path $tailwindPath)) {
    Write-Host "Tailwind binary not found. Installing standalone CLI..."
    npm install -D tailwindcss@3
}

Write-Host "Initializing Tailwind config..."
npx tailwindcss init -p

Write-Host "Done. Tailwind ready."
