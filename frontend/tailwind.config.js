/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  darkMode: 'class',
  theme: {
    screens: {
      sm: '575px',
      md: '768px',
      lg: '1025px',
      xl: '1202px',
    },
    extend: {
      colors: {
        primary: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
        },
        accent: '#8358FF',
        'accent-dark': '#7444FF',
        'accent-light': '#9E7CFF',
        'accent-lighter': '#B9A0FF',
        jacarta: {
          base: '#5A5D79',
          50: '#F4F4F6',
          100: '#E7E8EC',
          200: '#C4C5CF',
          300: '#A1A2B3',
          400: '#7D7F96',
          500: '#5A5D79',
          600: '#363A5D',
          700: '#131740',
          800: '#101436',
          900: '#0D102D',
        },
      },
      fontFamily: {
        display: ['"CalSans-SemiBold"', 'sans-serif'],
        body: ['"DM Sans"', 'sans-serif'],
      },
      borderRadius: {
        '2lg': '0.625rem',
        '2.5xl': '1.25rem',
      },
      boxShadow: {
        'accent-volume': '5px 5px 10px rgba(108, 106, 213, 0.25), inset 2px 2px 6px #A78DF0, inset -5px -5px 10px #6336E4',
        'white-volume': '5px 5px 10px rgba(108, 106, 212, 0.25), inset 2px 2px 6px #EEF1F9, inset -5px -5px 10px #DFE3EF',
      },
      animation: {
        fly: 'fly 6s cubic-bezier(0.75, 0.02, 0.31, 0.87) infinite',
        gradient: 'gradient 6s linear infinite',
        gradientDiagonal: 'gradientDiagonal 6s linear infinite',
      },
      keyframes: {
        fly: {
          '0%, 100%': { transform: 'translateY(5%)' },
          '50%': { transform: 'translateY(-5%)' },
        },
        gradient: {
          '0%, 100%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' },
        },
        gradientDiagonal: {
          '0%': { transform: 'translate(-50%, -50%) rotate(0deg)' },
          '100%': { transform: 'translate(-50%, -50%) rotate(360deg)' },
        },
      },
    },
  },
  plugins: [],
}
