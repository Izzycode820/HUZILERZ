/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  darkMode: 'class', // Enable class-based dark mode
  theme: {
    extend: {
      colors: {
        'huzilerz-black': '#050505',
        'huzilerz-lime': '#D4FF00',
        'huzilerz-gray': '#1A1A1A',
        background: 'var(--background)',
        foreground: 'var(--foreground)',
        // Dark mode color palette
        dark: {
          bg: '#0f172a',       // slate-900
          surface: '#1e293b',   // slate-800
          card: '#334155',      // slate-700
          border: '#475569',    // slate-600
          text: '#f1f5f9',      // slate-100
          muted: '#94a3b8',     // slate-400
        },
        // Brand colors for HustlerzCamp
        brand: {
          primary: '#059669',   // emerald-600
          secondary: '#0d9488', // teal-600
          accent: '#7c3aed',    // violet-600
        }
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'skeleton-wave': 'skeletonWave 1.6s ease-in-out infinite',
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
        skeletonWave: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
      },
    },
  },
  plugins: [],
}