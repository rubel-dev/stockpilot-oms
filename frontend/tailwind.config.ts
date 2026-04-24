import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./features/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        background: "#f5f7fb",
        foreground: "#101828",
        surface: "#ffffff",
        muted: "#667085",
        border: "#e4e7ec",
        brand: {
          50: "#eef4ff",
          100: "#dbe8ff",
          500: "#2e6cf6",
          600: "#1e5ae7",
          700: "#1948bb"
        },
        success: "#039855",
        warning: "#dc6803",
        danger: "#d92d20"
      },
      boxShadow: {
        soft: "0 1px 2px rgba(16, 24, 40, 0.04), 0 12px 24px rgba(16, 24, 40, 0.06)"
      },
      borderRadius: {
        xl: "0.875rem"
      }
    }
  },
  plugins: []
};

export default config;

