import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#ecfeff",
          100: "#cffafe",
          200: "#a5f3fc",
          300: "#67e8f9",
          400: "#22d3ee",
          500: "#06b6d4",
          600: "#0891b2",
          700: "#0e7490",
          800: "#155e75",
          900: "#164e63",
          950: "#083344",
        },
        surface: {
          0: "hsl(var(--surface-0))",
          1: "hsl(var(--surface-1))",
          2: "hsl(var(--surface-2))",
          3: "hsl(var(--surface-3))",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        display: ["Syne", "Inter", "system-ui", "sans-serif"],
      },
      maxWidth: {
        container: "1400px",
      },
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        "hero-glow": "radial-gradient(ellipse 80% 50% at 50% -20%, rgba(6,182,212,0.10), transparent)",
        "card-shine": "linear-gradient(135deg, rgba(255,255,255,0.02) 0%, transparent 50%)",
      },
      boxShadow: {
        glow: "0 0 20px rgba(6,182,212,0.15)",
        "glow-lg": "0 0 40px rgba(6,182,212,0.2)",
        card: "0 1px 2px rgba(0,0,0,0.2)",
        "card-hover": "0 8px 24px rgba(0,0,0,0.3), 0 0 12px rgba(6,182,212,0.06)",
      },
      borderRadius: {
        "2xl": "1rem",
        "3xl": "1.5rem",
      },
      animation: {
        "fade-in": "fade-in 0.4s ease-out both",
        "slide-up": "slide-up 0.4s ease-out both",
        shimmer: "shimmer 2s linear infinite",
        float: "float 6s ease-in-out infinite",
        shake: "shake 0.5s ease-in-out",
      },
      keyframes: {
        "fade-in": {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "slide-up": {
          "0%": { opacity: "0", transform: "translateY(16px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-10px)" },
        },
        shake: {
          "0%, 100%": { transform: "translateX(0)" },
          "15%": { transform: "translateX(-4px)" },
          "30%": { transform: "translateX(4px)" },
          "45%": { transform: "translateX(-3px)" },
          "60%": { transform: "translateX(3px)" },
          "75%": { transform: "translateX(-1px)" },
          "90%": { transform: "translateX(1px)" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
