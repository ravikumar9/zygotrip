Write-Host "Building Tailwind CSS..."

npx tailwindcss `
 -i ./static_src/input.css `
 -o ./static/css/tailwind.css `
 --watch
