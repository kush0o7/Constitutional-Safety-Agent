/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: '#0c1524',
        mist: '#f5f7fb',
        accent: '#d97706',
        sea: '#0f766e',
        danger: '#b91c1c'
      },
      fontFamily: {
        display: ['Space Grotesk', 'sans-serif'],
        body: ['IBM Plex Sans', 'sans-serif']
      }
    }
  },
  plugins: []
};
