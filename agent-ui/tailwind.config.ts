import type { Config } from 'tailwindcss'
import tailwindcssAnimate from 'tailwindcss-animate'

export default {
  darkMode: ['class'],
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}'
  ],
  theme: {
  	extend: {
  		colors: {
  			primary: {
  				DEFAULT: '#e5e5e5',
  				foreground: '#18181B'
  			},
  			primaryAccent: '#18181B',
  			brand: '#FF4017',
  			background: {
  				DEFAULT: '#1a1a1c',
  				secondary: '#27272A'
  			},
  			foreground: '#e5e5e5',
  			secondary: {
  				DEFAULT: '#d4d4d8',
  				foreground: '#18181B'
  			},
  			border: '#3f3f46',
  			accent: {
  				DEFAULT: '#27272A',
  				foreground: '#e5e5e5'
  			},
  			muted: {
  				DEFAULT: '#71717A',
  				foreground: '#a1a1aa'
  			},
  			destructive: {
  				DEFAULT: '#E53935',
  				foreground: '#FAFAFA'
  			},
  			positive: '#22C55E',
  			sidebar: {
  				DEFAULT: '#161618',
  				foreground: '#e5e5e5',
  				primary: '#e5e5e5',
  				'primary-foreground': '#161618',
  				accent: '#27272A',
  				'accent-foreground': '#e5e5e5',
  				border: '#3f3f46',
  				ring: '#3b82f6'
  			}
  		},
  		fontFamily: {
  			geist: 'var(--font-geist-sans)',
  			dmmono: 'var(--font-dm-mono)'
  		},
  		borderRadius: {
  			xl: '10px'
  		},
  		keyframes: {
  			'accordion-down': {
  				from: {
  					height: '0'
  				},
  				to: {
  					height: 'var(--radix-accordion-content-height)'
  				}
  			},
  			'accordion-up': {
  				from: {
  					height: 'var(--radix-accordion-content-height)'
  				},
  				to: {
  					height: '0'
  				}
  			}
  		},
  		animation: {
  			'accordion-down': 'accordion-down 0.2s ease-out',
  			'accordion-up': 'accordion-up 0.2s ease-out'
  		}
  	}
  },
  plugins: [tailwindcssAnimate]
} satisfies Config
