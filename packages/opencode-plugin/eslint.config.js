import js from "@eslint/js";
import tseslint from "typescript-eslint";

export default [
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    files: ["**/*.ts"],
    languageOptions: {
      globals: {
        fetch: "readonly",
        Response: "readonly",
        URL: "readonly",
        process: "readonly"
      }
    },
    rules: {
      "no-console": "error"
    }
  }
];
