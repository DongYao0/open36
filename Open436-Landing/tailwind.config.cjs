/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx}"],
  mode: "jit",
  theme: {
    extend: {
      colors: {
        primary: "rgb(var(--lc-primary) / <alpha-value>)",
        secondary: "rgb(var(--lc-secondary) / <alpha-value>)",
        tertiary: "rgb(var(--lc-tertiary) / <alpha-value>)",
        "white-100": "rgb(var(--lc-white100) / <alpha-value>)",
        "black-100": "#100d25",
        "black-200": "#090325",
      },
      boxShadow: {
        card: "0px 35px 120px -15px #211e35",
      },
      screens: {
        xs: "450px",
      },
      backgroundImage: {
        "hero-pattern": "url('/src/assets/herobg.png')",
      },
    },
  },
  plugins: [],
};
