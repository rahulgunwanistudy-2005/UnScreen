import js from '@eslint/js';
import svelte from 'eslint-plugin-svelte';
import globals from 'globals';
import ts from 'typescript-eslint';

export default ts.config(
	js.configs.recommended,
	...ts.configs.recommended,
	...svelte.configs.recommended,
	{
		languageOptions: { globals: { ...globals.browser, ...globals.node } }
	},
	{
		files: ['**/*.svelte', '**/*.svelte.ts', '**/*.ts'],
		languageOptions: {
			parserOptions: { parser: ts.parser, projectService: true, extraFileExtensions: ['.svelte'], tsconfigRootDir: import.meta.dirname }
		}
	},
	{
		rules: {
			'@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_', varsIgnorePattern: '^_' }]
		}
	},
	{ ignores: ['build/', '.svelte-kit/', 'node_modules/', 'test-results/', 'playwright-report/'] }
);
