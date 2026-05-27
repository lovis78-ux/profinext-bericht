/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        teal: {
          600: "#009BA5",
        },
        navy: {
          900: "#0C2561",
        },
        amber: {
          500: "#F5A31F",
        },
      },
    },
  },
  plugins: [],
};
