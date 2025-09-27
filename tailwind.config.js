/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: ['app/**/*.{ts,tsx}', 'components/**/*.{ts,tsx}'],
  theme: {
    extend: {
      keyframes: {
        fadeIn: {
          '0%': { opacity: 0, transform: 'translateY(10px)' },
          '100%': { opacity: 1, transform: 'translateY(0)' },
        },
      },
      animation: {
        fadeIn: 'fadeIn 0.2s ease-in-out',
      },
      fontFamily: {
        sans: ['var(--font-inter)', 'Inter', 'ui-sans-serif', 'system-ui'],
      },
      boxShadow: {
        subtle: '0 10px 30px -15px rgba(15, 23, 42, 0.25)',
      },
    },
  },
  plugins: [],
};
