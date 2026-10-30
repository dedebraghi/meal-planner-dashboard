import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        parchment: "#FAF9F6",
        culinary: {
          surface: "#FFFFFF",
          border: "#E7E5E4", // stone-200
          text: "#1A1A1A",   // near-black
          muted: "#78716C",  // stone-500
          sage: "#4A6B53",   // sage green accent
          terracotta: "#C25E3F",
          warm: "#F5F3EF",
        },
      },
      fontFamily: {
        serif: ["var(--font-serif)", "Playfair Display", "Georgia", "serif"],
        sans: ["var(--font-sans)", "Inter", "-apple-system", "BlinkMacSystemFont", "sans-serif"],
      },
    },
  },
  plugins: [],
};
export default config;
