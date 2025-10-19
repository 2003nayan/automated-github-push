/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Sophisticated neutrals - warm grays for light mode, cool charcoals for dark
        neutral: {
          50: '#FAFAFA',   // Light bg
          100: '#F4F4F5',  // Subtle bg
          200: '#E4E4E7',  // Border light
          300: '#D1D1D6',  // Border
          400: '#A1A1AA',  // Muted text
          500: '#71717A',  // Secondary text
          600: '#52525B',  // Text
          700: '#3F3F46',  // Dark border
          800: '#27272A',  // Dark card
          850: '#1F1F23',  // Dark elevated
          900: '#18181B',  // Dark bg
          950: '#09090B',  // Darkest
        },
        // Refined accent - subtle teal/blue for professional feel
        accent: {
          50: '#F0FDFA',
          100: '#CCFBF1',
          200: '#99F6E4',
          300: '#5EEAD4',
          400: '#2DD4BF',
          500: '#14B8A6',  // Main accent
          600: '#0D9488',
          700: '#0F766E',
          800: '#115E59',
          900: '#134E4A',
        },
        // Status colors - purposeful, not overwhelming
        success: {
          light: '#ECFDF5',
          DEFAULT: '#10B981',
          dark: '#059669',
        },
        warning: {
          light: '#FFFBEB',
          DEFAULT: '#F59E0B',
          dark: '#D97706',
        },
        error: {
          light: '#FEF2F2',
          DEFAULT: '#EF4444',
          dark: '#DC2626',
        },
        info: {
          light: '#EFF6FF',
          DEFAULT: '#3B82F6',
          dark: '#2563EB',
        },
      },
      boxShadow: {
        'minimal': '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
        'card': '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
        'card-hover': '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
        'elevated': '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-in-out',
        'slide-up': 'slideUp 0.4s ease-out',
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
      borderRadius: {
        'sm': '0.25rem',
        'DEFAULT': '0.375rem',
        'lg': '0.5rem',
        'xl': '0.75rem',
      },
    },
  },
  plugins: [],
  darkMode: 'class',
}
