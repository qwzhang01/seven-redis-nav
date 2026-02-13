/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{vue,js,ts,jsx,tsx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#e6fcff',
          100: '#b3f5ff',
          200: '#80eeff',
          300: '#4de7ff',
          400: '#1ae0ff',
          500: '#00d4ff',
          600: '#00b8db',
          700: '#008fa8',
          800: '#006675',
          900: '#003d42',
        },
        accent: {
          cyan: '#00d4ff',
          blue: '#3b82f6',
          purple: '#8b5cf6',
          green: '#10b981',
          red: '#ef4444',
          orange: '#f59e0b',
        },
        dark: {
          900: '#0a0e17',
          800: '#0f1420',
          700: '#141a2a',
          600: '#1a2035',
          500: '#1e2640',
          400: '#252d45',
          300: '#2d3752',
          200: '#3a4568',
          100: '#4a5680',
        },
        white: '#ffffff',
      },
      fontFamily: {
        sans: ['Inter', 'Noto Sans SC', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'hero-glow': 'radial-gradient(ellipse at 50% 0%, rgba(0, 212, 255, 0.15) 0%, transparent 60%)',
        'card-glow': 'radial-gradient(ellipse at 50% 0%, rgba(0, 212, 255, 0.08) 0%, transparent 70%)',
      },
      boxShadow: {
        'glow-sm': '0 0 15px rgba(0, 212, 255, 0.1)',
        'glow-md': '0 0 30px rgba(0, 212, 255, 0.15)',
        'glow-lg': '0 0 60px rgba(0, 212, 255, 0.2)',
        'card': '0 4px 24px rgba(0, 0, 0, 0.3)',
      },
      animation: {
        'glow-pulse': 'glow-pulse 3s ease-in-out infinite',
        'float': 'float 6s ease-in-out infinite',
        'fade-in-up': 'fade-in-up 0.6s ease-out forwards',
      },
      keyframes: {
        'glow-pulse': {
          '0%, 100%': { boxShadow: '0 0 20px rgba(0, 212, 255, 0.1)' },
          '50%': { boxShadow: '0 0 40px rgba(0, 212, 255, 0.25)' },
        },
        'float': {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        'fade-in-up': {
          from: { opacity: '0', transform: 'translateY(20px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
}
