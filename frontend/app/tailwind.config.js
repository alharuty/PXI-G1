module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#FDFC9C',
          100: '#00AFB9',
          200: '#0081A7',
          300: '#FED9B7',
          400: '#F07167',
        },
        dark: {
          900: '#0f172a', // Muy oscuro
          800: '#1e293b', // Oscuro
          700: '#334155', // Medio oscuro
          600: '#475569', // Gris oscuro
        }
      },
      fontFamily: {
        'sans': ['system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
      }
    },
  },
  plugins: [],
}