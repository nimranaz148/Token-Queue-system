import nextPlugin from "@next/eslint-plugin-next";
import tsParser from "@typescript-eslint/parser";

const eslintConfig = [
  {
    ignores: [".next/**", "node_modules/**", "coverage/**", "out/**"],
  },
  {
    files: ["**/*.{ts,tsx}"],
    languageOptions: {
      parser: tsParser,
      parserOptions: {
        ecmaVersion: "latest",
        sourceType: "module",
        ecmaFeatures: {
          jsx: true,
        },
      },
    },
    plugins: {
      "@next/next": nextPlugin,
    },
    rules: {
      ...nextPlugin.configs.recommended.rules,
      ...nextPlugin.configs["core-web-vitals"].rules,
      "no-restricted-syntax": [
        "error",
        {
          selector: "CallExpression[callee.property.name='from']",
          message:
            "Forbidden: supabase.from(...) database calls are not permitted in apps/web. Only apps/api may read or write the database.",
        },
      ],
    },
  },
];

export default eslintConfig;
