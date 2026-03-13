/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                background: '#09090b', // Zinc 950
                surface: '#18181b',    // Zinc 900
                primary: '#10b981',    // Emerald 500 (Valid)
                danger: '#ef4444',     // Red 500 (Invalid)
                warning: '#f59e0b',    // Amber 500 (Review)
                accent: '#8b5cf6',     // Violet 500 (UI Highlights)
            },
            fontFamily: {
                sans: ['Inter', 'sans-serif'],
            },
        },
    },
    plugins: [],
}
