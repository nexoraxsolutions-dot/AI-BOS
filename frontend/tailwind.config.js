/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    './app/**/*.{js,ts,jsx,tsx}',
    './components/**/*.{js,ts,jsx,tsx}',
    './context/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: [
          'var(--font-inter)',
          'Inter',
          'ui-sans-serif',
          'system-ui',
          '-apple-system',
          'BlinkMacSystemFont',
          'Segoe UI',
          'sans-serif',
        ],
      },
      colors: {
        // ---- AI-BOS Brand ----
        brand: {
          50: '#F4F5FF',
          100: '#EEF2FF',
          200: '#E0E7FF',
          300: '#C7D2FE',
          400: '#A5B4FC',
          500: '#8B5CF6', // secondary purple accent
          600: '#635BFF', // primary accent (Electric Violet)
          700: '#4F46E5', // primary hover / gradient stop
          800: '#4338CA',
          900: '#3730A3',
        },
        primary: {
          DEFAULT: '#635BFF',
          hover: '#4F46E5',
          light: '#EEF2FF',
          soft: '#F4F5FF',
        },
        secondary: {
          DEFAULT: '#8B5CF6',
        },
        // ---- Light theme surfaces ----
        surface: {
          DEFAULT: '#FFFFFF',
          subtle: '#F8FAFC',
          alt: '#F4F6F8',
          border: '#E2E8F0',
        },
        sidebar: {
          DEFAULT: '#0A0E27', // deep midnight navy
          alt: '#0B1220',
          hover: '#1E293B',
          border: '#1E293B',
        },
        ink: {
          DEFAULT: '#0F172A', // text primary (light)
          muted: '#64748B', // text secondary (light)
        },
        // ---- Dark theme surfaces ----
        dark: {
          bg: '#0B0E14', // deep obsidian
          surface: '#121824',
          border: '#1E293B',
          text: '#F8FAFC',
          muted: '#94A3B8',
        },
      },
      boxShadow: {
        card: '0 1px 3px 0 rgb(15 23 42 / 0.06), 0 1px 2px -1px rgb(15 23 42 / 0.06)',
        cardLg: '0 4px 24px -2px rgb(15 23 42 / 0.08), 0 2px 6px -2px rgb(15 23 42 / 0.06)',
        glow: '0 8px 30px -4px rgb(99 91 255 / 0.35)',
        active: '0 8px 20px -6px rgb(79 70 229 / 0.55)',
      },
      borderRadius: {
        xl: '0.875rem',
        '2xl': '1.25rem',
      },
      backgroundImage: {
        'brand-gradient': 'linear-gradient(135deg, #635BFF 0%, #4F46E5 100%)',
        'brand-gradient-soft': 'linear-gradient(135deg, #F4F5FF 0%, #EEF2FF 100%)',
        'logo-gradient': 'linear-gradient(135deg, #635BFF 0%, #8B5CF6 50%, #4F46E5 100%)',
        'sidebar-gradient': 'linear-gradient(180deg, #0A0E27 0%, #0B1220 100%)',
      },
      keyframes: {
        'slide-in': {
          '0%': { transform: 'translateX(100%)' },
          '100%': { transform: 'translateX(0)' },
        },
        'slide-out': {
          '0%': { transform: 'translateX(0)' },
          '100%': { transform: 'translateX(100%)' },
        },
        'fade-in': {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        'pulse-soft': {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.6' },
        },
        shimmer: {
          '100%': { transform: 'translateX(100%)' },
        },
      },
      animation: {
        'slide-in': 'slide-in 0.3s ease-out',
        'fade-in': 'fade-in 0.25s ease-out',
        'pulse-soft': 'pulse-soft 2s ease-in-out infinite',
      },
    },
  },
  plugins: [],
};
