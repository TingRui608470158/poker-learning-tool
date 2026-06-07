/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        "felt-dark": "#1a4d3e",
        "felt-mid": "#2d6a4f",
        "felt-border": "#40916c",
        accent: "#ffd166",
        "card-face": "#fefefe",
        "card-back": "#1d3557",
        muted: "#b7e4c7",
        surface: "#0f1f1a",
      },
    },
  },
  plugins: [],
};
