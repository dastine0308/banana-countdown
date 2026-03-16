import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        display: ["var(--font-display)"],
        body: ["var(--font-body)"],
        mono: ["var(--font-mono)", "monospace"],
      },
      colors: {
        banana: {
          50:  "#fffde7",
          100: "#fff9c4",
          200: "#fff59d",
          300: "#fff176",
          400: "#ffee58",
          500: "#ffeb3b",
          600: "#fdd835",
          700: "#f9a825",
          800: "#f57f17",
          900: "#e65100",
        },
        ripe:      "#4caf50",
        overripe:  "#ff9800",
        rotten:    "#f44336",
        unripe:    "#8bc34a",
      },
    },
  },
  plugins: [],
};
export default config;
