#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const postcss = require('postcss');
const tailwindPostCss = require('@tailwindcss/postcss');
const autoprefixer = require('autoprefixer');

const inputPath = path.join(__dirname, 'static/css/input.css');
const outputPath = path.join(__dirname, 'static/css/tailwind.css');

const inputCss = fs.readFileSync(inputPath, 'utf8');

postcss([
  tailwindPostCss,
  autoprefixer
])
  .process(inputCss, {
    from: inputPath,
    to: outputPath,
  })
  .then(result => {
    fs.writeFileSync(outputPath, result.css);
    console.log(`✅ Tailwind CSS built successfully: ${outputPath}`);
    console.log(`📊 Generated file size: ${result.css.length} bytes`);
    process.exit(0);
  })
  .catch(err => {
    console.error('❌ Build failed:', err.message);
    process.exit(1);
  });
