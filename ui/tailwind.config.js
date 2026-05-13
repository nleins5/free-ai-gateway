/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        void: 'rgb(var(--color-void) / <alpha-value>)',
        sidebar: 'rgb(var(--color-sidebar) / <alpha-value>)',
        input: 'rgb(var(--color-input) / <alpha-value>)',
        plasma: 'rgb(var(--color-plasma) / <alpha-value>)',
        ghost: 'rgb(var(--color-ghost) / <alpha-value>)',
        graphite: 'rgb(var(--color-graphite) / <alpha-value>)'
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        serif: ['Playfair Display', 'serif'],
        mono: ['JetBrains Mono', 'monospace']
      }
    },
  },
  plugins: [],
}
