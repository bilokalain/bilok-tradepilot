/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        background: "#000000",
        card: "#0A0A0A",
        surface: "#141414",
        border: "#1F1F1F",
        gold: {
          DEFAULT: "#D4AF37",
          light: "#F5D060",
          dark: "#B8960C",
        },
        text: {
          primary: "#FFFFFF",
          secondary: "#A0A0A0",
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
