/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // User requested palette
        powder: {
          50: '#f1f6fd',
          100: '#e2edfb',
          200: '#c5dcf7',
          300: '#adcff6',
          400: '#8DB9F0', // Main Powder Blue
          500: '#6ea6ec',
          600: '#4e8fe2',
          700: '#3575cb',
          800: '#22559c',
          900: '#1a3d6d',
        },
        lavender: {
          50: '#faf9fd',
          100: '#f4f3fb',
          200: '#E9E8F8', // Main Soft Lavender White
          300: '#d7d4f2',
          400: '#bfb9e9',
          500: '#a399de',
          600: '#8374cf',
          700: '#6755b9',
          800: '#524398',
          900: '#43377c',
        },
        peach: {
          50: '#fef7f4',
          100: '#fdeee8',
          200: '#fbd8cc',
          300: '#fad1c2',
          400: '#F5B69E', // Main Warm Sunset Peach
          500: '#ea9e80',
          600: '#d88160',
          700: '#be6543',
          800: '#9b5136',
          900: '#7c432f',
        },
      },
      fontFamily: {
        sans: ['Plus Jakarta Sans', 'system-ui', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
