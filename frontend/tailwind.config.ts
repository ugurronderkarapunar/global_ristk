// frontend/tailwind.config.ts
import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Finans terminali renk paleti
        'terminal-bg': '#0a0e17',
        'terminal-card': '#1a1f2e',
        'terminal-border': '#2a3040',
        'terminal-accent': '#3a8bff',
        'terminal-text': '#e0e6f0',
        'terminal-muted': '#6b7280',
        'risk-high': '#ff4444',
        'risk-medium': '#ffaa00',
        'risk-low': '#00cc66',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
        arabic: ['Noto Naskh Arabic', 'Traditional Arabic', 'serif'],
        chinese: ['Noto Sans SC', 'Microsoft YaHei', 'sans-serif'],
      },
      animation: {
        'pulse-glow': 'pulseGlow 2s ease-in-out infinite',
        'slide-up': 'slideUp 0.3s ease-out',
      },
      keyframes: {
        pulseGlow: {
          '0%, 100%': { boxShadow: '0 0 5px rgba(58, 139, 255, 0.2)' },
          '50%': { boxShadow: '0 0 20px rgba(58, 139, 255, 0.5)' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
    },
  },
  plugins: [
    require('tailwindcss-rtl'), // RTL desteği için
    require('@tailwindcss/typography'),
  ],
};

export default config;
