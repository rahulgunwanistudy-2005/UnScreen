import { defineConfig } from '@playwright/test';

export default defineConfig({
	testDir: 'tests',
	timeout: 60_000,
	use: { baseURL: 'http://localhost:4173' },
	webServer: [
		{
			// The app under test, built to talk to the loop-test engine below.
			command: 'VITE_ENGINE_URL=http://localhost:8788 pnpm build && pnpm preview --port 4173 --strictPort',
			port: 4173,
			reuseExistingServer: !process.env.CI
		},
		{
			// The shipped engine with a scripted vision model (services/engine/tests/e2e_app.py).
			command: 'cd ../../services/engine && uv run uvicorn tests.e2e_app:app --port 8788',
			url: 'http://localhost:8788/healthz',
			reuseExistingServer: !process.env.CI
		}
	]
});
