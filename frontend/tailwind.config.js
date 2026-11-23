/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        background: '#000000',
        surface: '#0A0A0A',
        elevated: '#111111',
        glass: 'rgba(255, 255, 255, 0.035)',
        'glass-border': 'rgba(255, 255, 255, 0.10)',
        'text-primary': '#FFFFFF',
        'text-secondary': '#A3A3A3',
        'text-muted': '#737373',
        'risk-low': '#70C8A0',
        'risk-mod': '#E9BF72',
        'risk-high': '#E88C8C',
      },
      fontFamily: {
        sans: ['Geist', 'Inter', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
