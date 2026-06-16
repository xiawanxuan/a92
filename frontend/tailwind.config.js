/** @type {import('tailwindcss').Config} */

export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,ts,vue}"],
  theme: {
    container: {
      center: true,
    },
    extend: {
      colors: {
        'deep-ocean': {
          50: '#f0f7ff',
          100: '#e0efff',
          200: '#bae0ff',
          300: '#7cc5ff',
          400: '#36a7ff',
          500: '#0c8aff',
          600: '#006de0',
          700: '#0057b6',
          800: '#0A2463',
          900: '#071a47',
          950: '#040f2b',
        },
        'tech-cyan': '#3E92CC',
        'warning-orange': '#F46036',
        'data-green': '#1B998B',
        'substrate': {
          'sediment': '#D4A574',
          'rock': '#6B7280',
          'coral': '#E63946',
          'man-made': '#FFD700',
        }
      },
      fontFamily: {
        'mono': ['JetBrains Mono', 'monospace'],
        'sans': ['Noto Sans SC', 'sans-serif'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'fade-in': 'fadeIn 0.3s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
      boxShadow: {
        'glass': '0 8px 32px rgba(10, 36, 99, 0.2)',
      }
    },
  },
  plugins: [],
};
