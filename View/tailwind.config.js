/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'perano': {
          '50': '#ffffff',
          '100': '#e9f2ff',
          '200': '#d4e5ff',
          '300': '#cee3ff',
          '400': '#b6d7ff',
          '500': '#89c3ff',
          '600': '#4ea3ff',
          '700': '#3c7fcf',
          '800': '#275791',
          '900': '#0f2e52',
          '950': '#091f3a',
        }
      }
    },
  },
  plugins: [],
}

