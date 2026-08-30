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
        canvas: "#F0F0F0",
        foreground: "#121212",
        "bauhaus-red": "#D02020",
        "bauhaus-blue": "#1040C0",
        "bauhaus-yellow": "#F0C020",
        "bauhaus-black": "#121212",
        "bauhaus-muted": "#E0E0E0",
        "bauhaus-light-yellow": "#FFF9C4",
      },
      fontFamily: {
        sans: ["var(--font-outfit)", "Outfit", "system-ui", "sans-serif"],
        display: ["var(--font-outfit)", "Outfit", "system-ui", "sans-serif"],
      },
      boxShadow: {
        "bauhaus-sm": "4px 4px 0px 0px #121212",
        "bauhaus-md": "6px 6px 0px 0px #121212",
        "bauhaus-lg": "8px 8px 0px 0px #121212",
        "bauhaus-sm-white": "4px 4px 0px 0px #FFFFFF",
        "bauhaus-md-white": "6px 6px 0px 0px #FFFFFF",
        "bauhaus-lg-white": "8px 8px 0px 0px #FFFFFF",
      },
      borderWidth: {
        "2": "2px",
        "3": "3px",
        "4": "4px",
        "6": "6px",
        "8": "8px",
      },
      borderRadius: {
        none: "0px",
        full: "9999px",
      },
    },
  },
  plugins: [],
};

export default config;
