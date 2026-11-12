/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,ts}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#eafaf7',
          100: '#cdf3ec',
          200: '#9ee8da',
          300: '#65d5c2',
          400: '#35bda7',
          500: '#18a18c',
          600: '#0e9180',
          700: '#0d7469',
          800: '#0d5c55',
          900: '#0c4c47',
        },
        surface: {
          50: '#f6f9fb',
          100: '#eef4f7',
          200: '#e4edf2',
        },
        navy: {
          700: '#153a68',
          800: '#0d2a51',
          900: '#081c38',
        },
        teal: {
          100: '#d5f5ef',
          400: '#38c7b0',
          500: '#14a992',
          600: '#0d8b78',
        },
        ink: {
          50: '#f8fafc',
          100: '#f1f5f9',
          200: '#e2e8f0',
          300: '#cbd5e1',
          400: '#94a3b8',
          500: '#64748b',
          600: '#475569',
          700: '#334155',
          800: '#1e293b',
          900: '#0f172a',
        },
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', '-apple-system', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
      borderRadius: {
        xl: '0.875rem',
        '2xl': '1.25rem',
      },
      boxShadow: {
        card: '0 1px 2px rgba(15,23,42,0.04), 0 8px 24px -12px rgba(15,23,42,0.12)',
        lift: '0 8px 30px -12px rgba(20,169,146,0.4)',
        glow: '0 0 0 1px rgba(14,145,128,0.18), 0 12px 40px -14px rgba(14,145,128,0.45)',
      },
      keyframes: {
        'fade-up': {
          '0%': { opacity: '0', transform: 'translateY(6px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'grow-x': {
          '0%': { transform: 'scaleX(0)' },
          '100%': { transform: 'scaleX(1)' },
        },
        'gradient-x': {
          '0%, 100%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' },
        },
        shimmer: {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(200%)' },
        },
        'pop-in': {
          '0%': { opacity: '0', transform: 'scale(0.92)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
      },
      animation: {
        'fade-up': 'fade-up 0.35s ease-out both',
        'grow-x': 'grow-x 1s cubic-bezier(0.22, 1, 0.36, 1) both',
        'gradient-x': 'gradient-x 6s ease infinite',
        'pop-in': 'pop-in 0.25s cubic-bezier(0.22, 1, 0.36, 1) both',
      },
    },
  },
  plugins: [],
};
