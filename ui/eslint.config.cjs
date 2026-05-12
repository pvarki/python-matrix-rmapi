const { defineConfig, globalIgnores } = require("eslint/config");

const globals = require("globals");

const { fixupConfigRules } = require("@eslint/compat");

const tsParser = require("@typescript-eslint/parser");
const reactRefresh = require("eslint-plugin-react-refresh");
const js = require("@eslint/js");

const { FlatCompat } = require("@eslint/eslintrc");

const compat = new FlatCompat({
  baseDirectory: __dirname,
  recommendedConfig: js.configs.recommended,
  allConfig: js.configs.all,
});

module.exports = defineConfig([
  {
    languageOptions: {
      globals: {
        ...globals.browser,
      },

      parser: tsParser,
      ecmaVersion: "latest",
      sourceType: "module",

      parserOptions: {
        project: true,
        tsconfigRootDir: __dirname,
      },
    },

    extends: fixupConfigRules(
      compat.extends(
        "eslint:recommended",
        "plugin:@typescript-eslint/recommended",
        "plugin:@typescript-eslint/recommended-requiring-type-checking",
        "plugin:react-hooks/recommended",
      ),
    ),

    plugins: {
      "react-refresh": reactRefresh,
    },

    rules: {
      "react-refresh/only-export-components": [
        "warn",
        {
          allowConstantExport: true,
        },
      ],

      "@typescript-eslint/no-non-null-assertion": "off",
    },
  },
  globalIgnores([
    "dist/**/*",
    "scripts/**/*",
    "**/.eslintrc.cjs",
    "eslint.config.cjs",
    "**/vite.config.ts",
    "**/tailwind.config.js",
    "src/mocks/**/*",
    "**/mocksBrowser.ts",
    "public/mockServiceWorker.js",
  ]),
]);
