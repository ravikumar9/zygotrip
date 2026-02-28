const { defineConfig } = require('@playwright/test');

module.exports = defineConfig({
  testDir: './tests',
  timeout: 60000,
  use: {
    baseURL: 'https://127.0.0.1:8000',
    headless: false,
    ignoreHTTPSErrors: true,
    actionTimeout: 8000,
    navigationTimeout: 30000,
    viewport: { width: 1280, height: 800 },
    launchOptions: {
      slowMo: 100,
    },
  },
  projects: [
    {
      name: 'chromium',
      use: { browserName: 'chromium' },
    },
  ],
});
