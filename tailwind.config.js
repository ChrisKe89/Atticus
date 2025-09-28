/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    'app/**/*.{ts,tsx,mdx}',
    'components/**/*.{ts,tsx}',
    'lib/**/*.{ts,tsx}',
    'content/**/*.{md,mdx}',
    'docs/**/*.{md,mdx}',
  ],
  theme: {
    extend: {
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
