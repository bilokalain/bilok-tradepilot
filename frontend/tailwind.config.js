/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        background: "var(--color-background, #000000)",
        card: "var(--color-card, #0A0A0A)",
        surface: "var(--color-surface, #141414)",
        border: "var(--color-border, #1F1F1F)",
        gold: {
          DEFAULT: "var(--color-accent, #D4AF37)",
          light: "var(--color-accent-light, #F5D060)",
          dark: "var(--color-accent-dark, #B8960C)",
        },
        text: {
          primary: "var(--color-text-primary, #FFFFFF)",
          secondary: "var(--color-text-secondary, #A0A0A0)",
        },
      },
      fontFamily: {
        sans: ["Inter", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
    },
  },
  plugins: [],
};
