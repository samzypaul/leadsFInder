import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: "#0d9488", // teal-600
          dark: "#0f766e",
          light: "#14b8a6",
        },
      },
    },
  },
  plugins: [],
};

export default config;
