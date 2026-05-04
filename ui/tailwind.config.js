/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        void: '#0A0A14',
        plasma: '#7B61FF',
        ghost: '#F0EFF4',
        graphite: '#18181B'
      },
      fontFamily: {
        sans: ['Sora', 'sans-serif'],
        serif: ['Instrument Serif', 'serif'],
        mono: ['Fira Code', 'monospace']
      }
    },
  },
  plugins: [],
}
